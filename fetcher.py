#!/usr/bin/env python
# encoding: utf-8

"""Poll put.io for new tv show videos and download them automatically.

Organizes files into directories like: <show>/<season #>/<episode>
Supports multiple parallel downloads as well as resuming broken downloads.
"""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from gevent import monkey; monkey.patch_all()

from contextlib import contextmanager
import logging as log
import os
import re
import shutil
import time

import gevent, gevent.pool
import putio
import requests
import yaml

class AttrDict(dict):
  """The most minimal possible implementation of a nested dot-notation dict."""
  def __getattr__(self, name):
    return AttrDict(self[name]) if isinstance(self[name], dict) else self[name]

CFG = AttrDict(yaml.load(open('cfg.yml', 'r')))

log.root.setLevel(CFG.loglevel)
_word, _type = CFG.match.word, CFG.match.type
show_pattern = r'^(%s+)[.][Ss](\d{2})[Ee](\d{2})(%s+)[.](%s)$' % (_word, _word, _type)
show_re = re.compile(show_pattern)
range_re = re.compile(r'bytes (\d+)-\d+/\d+')

api = putio.Api(CFG.putio.api_key, CFG.putio.api_secret)
down_path = os.path.expanduser(CFG.download.local)
down_put_path = CFG.download.putio
down_put_dir = None

def episode_sort_key(it):
  """Extract season and episode from show titles for numeric sorting."""
  match = show_re.match(it.name)
  if not match: return it.name
  _, season, episode, _, _ = match.groups()
  return (int(season), int(episode))

def get_all_videos(parent=0):
  """Put.io's api is a bit broken, so manually find all videos recursively."""
  videos = []
  try:
    videos.extend(api.get_items(type='movie', parent_id=parent))
  except putio.PutioError: pass

  try:
    for subdir in api.get_items(type='folder', parent_id=parent):
      videos.extend(get_all_videos(parent=subdir.id))
  except putio.PutioError: pass

  return videos

def fetch_to_file(url, path, size=None):
  """Do the low-level transfer from a url to a file, supporting resume."""
  chunk_size = CFG.io.chunk

  start = 0
  if size and os.path.exists(path):
    start = os.path.getsize(path)
    if start == size:
      log.info('Already finished "%s"! Skipping.', path)
      return True
    log.info('Found %s already downloaded, resuming.', putio.human_size(start))

  params = {
      'auth': (CFG.putio.user, CFG.putio.password),
      'prefetch': False,
      'headers': {'Range': 'bytes=%d-' % start, 'User-Agent': CFG.user_agent},
  }

  try:
    response = requests.get(url, **params)
    if response.status_code not in (200, 206):
      log.error('Bad status code %d for "%s".', response.status_code, url)
      return False

    match = range_re.match(response.headers.get('content-range', ''))
    if match:
      server_start = int(match.group(1))
      if server_start != start:
        log.warning('Server returned unexpected range: %d.', server_start)
        start = min(start, server_start)  # Avoid seeking past end of file

    with open(path, 'ab') as dl_file:
      shutil.copyfileobj(response.raw, dl_file, chunk_size)

  except requests.exceptions.RequestException as re:
    log.error('Error downloading "%s": %s.', path, re)
    return False

  return True

def fetch(label, url, path, it):
  """Manage the download from put.io, then move to downloaded folder."""
  log.info('Downloading %s from "%s" to "%s".', label, url, path)

  file_dir, file_name = os.path.split(path)
  if not os.path.exists(file_dir):
    log.info('Download dir "%s" not found, creating.', file_dir)
    os.makedirs(file_dir)

  max_tries = CFG.io.retry.count
  for tries in xrange(1, max_tries + 1):
    log.info('Download attempt #%d of "%s".', tries, url)
    if fetch_to_file(url, path, int(it.size)):
      break
    time.sleep(CFG.io.retry.delay)

  if tries == max_tries:
    log.info('Completely failed to download "%s".', file_name)
    return False

  it.move_item(down_put_dir.id)
  log.info('Successfully downloaded "%s".', file_name)
  return True

def fetch_new():
  """Check for new video files in the put.io root folder and download."""
  global down_put_dir
  if not down_put_dir:
    try:
      down_put_dir = api.get_items(type='folder', name=down_put_path)[0]
      log.info('%s folder already in put.io, reusing.', down_put_path)
    except putio.PutioError:
      down_put_dir = api.create_folder(down_put_path)
      log.info('%s folder not found, created.', down_put_path)

  pool = gevent.pool.Pool(size=CFG.io.max)
  downloaded = 0

  try:
    # Find videos sitting in the root folder, and in watched folders.
    items = api.get_items(type='movie')
  except putio.PutioError:
    items = []

  for folder_name in CFG.watch.putio:
    try:
      folder = api.get_items(type='folder', name=folder_name)[0]
      sub_items = get_all_videos(folder.id)
      if not sub_items:
        # Confirm that it's really empty.
        try:
          all_sub_items = api.get_items(parent_id=folder.id)
        except putio.PutioError:
          log.info('Removing empty folder from watch folder: %s.', folder_name)
          #folder.delete_item()

      items.extend(sub_items)
    except putio.PutioError:
      down_put_dir = api.create_folder(down_put_path)
      log.warning('%s watch folder not found.', folder_name)

  # Sort by season and episode across all shows.
  items.sort(key=episode_sort_key)

  for it in items:
    name = it.name
    match = show_re.match(it.name)
    if match:
      name, season, episode, _, _ = match.groups()
      name = name.replace('.', ' ').replace('_', ' ').title()
      file_dir = os.path.join(down_path, name, 'Season %s' % season)
      label = '%s Season %s Episode %s' % (name, season, episode)
    else:
      file_dir = os.path.join(down_path, 'Videos')
      label = name

    file_path = os.path.join(file_dir, it.name)
    if not it.download_url:
      log.error('Empty download url for %s, put.io API issue.', label)
      continue

    g = pool.spawn(fetch, label, it.download_url, file_path, it)

  pool.join()
  return len(items)

if __name__ == '__main__':
  minutes = CFG.poll/60

  while True:
    try:
      if fetch_new():
        log.info('Fetched new episodes, waiting %d minutes.', minutes)
      else:
        log.info('No new episodes, waiting %d minutes.', minutes)
    except KeyboardInterrupt:
      log.info('Caught ctrl-c, shutting down.')
      break
    except putio.PutioError as pe:
      log.info('put.io reported an error, waiting %d minutes: %s', minutes, pe)

    time.sleep(CFG.poll)
