#!/usr/bin/env python
# encoding: utf-8

"""Poll put.io for new tv show videos and download them automatically.

Organizes files into directories like: <show>/<season #>/<episode>
Supports multiple parallel downloads as well as resuming broken downloads.
"""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from gevent import monkey; __name__ == '__main__' and monkey.patch_all()

from collections import namedtuple
from contextlib import contextmanager
import hashlib
import logging as log
import os
from gevent.queue import JoinableQueue as Queue
import re
import shutil
import stat
import subprocess
import time

import gevent, gevent.event, gevent.pool
import putio2 as putio
import requests
import yaml

from async import interval_block
from util import *


if not os.path.exists('cfg.yml'):
  shutil.copyfile('cfg.base.yml', 'cfg.yml')
CFG = AttrDict(yaml.load(open('cfg.yml', 'r')))

log.root.setLevel(CFG.loglevel)
_word, _type = CFG.match.word, CFG.match.type
show_pattern = r'^(%s+)[-_.][Ss]?(\d{1,2})[Eex](\d{1,2})(%s+)[.](%s)$' % (
    _word, _word, _type)
show_re = re.compile(show_pattern)
range_re = re.compile(r'bytes (\d+)-\d+/\d+')

api = None
converter_path = 'bin/SublerCLI'
convert_queue = Queue()
check_now = gevent.event.Event()
down_path = os.path.expanduser(CFG.download.local)
down_put_path = CFG.download.putio
down_put_dir = None
noop = lambda *args, **kwargs: None

# Patch these in to receive callbacks on file download events.
events = AttrDict({
    'init': noop,
    'status': noop,
    'progress': noop,
})

Download = namedtuple('Download', ('id', 'label', 'url', 'path', 'it'))

if not os.access(converter_path, os.X_OK):
  os.chmod(converter_path, os.stat(converter_path).st_mode | stat.S_IEXEC)

def load_api():
  global api, down_put_dir
  try:
    down_put_dir = None
    api = putio.Client(CFG.putio.access_token)
  except putio.PutioError:
    api = None
load_api()

def episode_sort_key(it):
  """Extract season and episode from show titles for numeric sorting."""
  match = show_re.match(it.name)
  if not match: return it.name
  _, season, episode, _, _ = match.groups()
  return (int(season), int(episode))

def convert_video(path, out='m4v'):
  path_name, ext = os.path.splitext(path)
  dest = '%s.%s' % (path_name, out)
  subprocess.call([converter_path, '-chapterspreview', '-downmix', 'stereo',
                   '-source', path, '-dest', dest])
  convert_queue.task_done()

def convert_worker():
  while True:
    path = convert_queue.get()
    gevent.spawn(convert_video, path)

@memoize(15)
def list_files_raw(parent):
  return api.File.list(parent_id=parent)

def list_files(kind=None, parent=0, name=None):
  files = list_files_raw(parent)
  if kind == 'folder': kind = 'application/x-directory'
  return [f for f in files if
          (not kind or f.content_type.startswith(kind)) and
          (not name or f.name == name)]

def get_all_videos(parent=0):
  """Put.io's api is a bit broken, so manually find all videos recursively."""
  videos = []
  try:
    videos.extend(list_files(kind='video', parent=parent))
  except putio.PutioError: pass

  try:
    for subdir in list_files(kind='folder', parent=parent):
      videos.extend(get_all_videos(parent=subdir.id))
  except putio.PutioError: pass

  return videos

def fetch_to_file(url, path, size=None, download=None):
  """Do the low-level transfer from a url to a file, supporting resume."""
  chunk_size = CFG.io.chunk

  start = 0
  if size and os.path.exists(path):
    start = os.path.getsize(path)
    if start == size:
      log.info('Already finished "%s"! Skipping.', path)
      return True
    log.info('Found %s already downloaded, resuming.', human_size(start))

  params = {
      'params': {'access_token': CFG.putio.access_token},
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
      def progress():
        cursize = os.path.getsize(path) if dl_file.closed else dl_file.tell()
        (download and events.progress)(download, cursize, size)

      with interval_block(progress, 0.25):
        shutil.copyfileobj(response.raw, dl_file, chunk_size)

  except requests.exceptions.RequestException as re:
    log.error('Error downloading "%s": %s.', path, re)
    return False

  return (size and os.path.getsize(path) == size) or True

def fetch(download):
  """Manage the download from put.io, then move to downloaded folder."""
  file_id, label, url, path, it = download
  log.info('Downloading %s from "%s" to "%s".', label, url, path)

  file_dir, file_name = os.path.split(path)
  if not os.path.exists(file_dir):
    log.info('Download dir "%s" not found, creating.', file_dir)
    os.makedirs(file_dir)

  (download and events.init)(download)

  success, max_tries = False, CFG.io.retry.count
  for tries in xrange(1, max_tries + 1):
    log.info('Download attempt #%d of "%s".', tries, url)
    (download and events.status)(download, 'downloading')

    if fetch_to_file(url, path, int(it.size), download):
      success = True
      break

    (download and events.status)(download, 'pending')
    time.sleep(CFG.io.retry.delay)

  if not success:
    log.info('Completely failed to download "%s".', file_name)
    (download and events.status)(download, 'failed')
    return False

  (download and events.status)(download, 'moving')
  it.move(down_put_dir.id)
  if False and CFG.download.remux:
    (download and events.status)(download, 'converting')
    convert_queue.put(path)
  log.info('Successfully downloaded "%s".', file_name)
  (download and events.status)(download, 'completed')
  return True

def fetch_new():
  """Check for new video files in the put.io root folder and download."""
  global down_put_dir
  if not api:
    log.error('Failed to connect to put.io api.')
    return 0
  if not down_put_dir:
    try:
      down_put_dir = list_files(kind='folder', name=down_put_path)[0]
      log.info('%s folder already in put.io, reusing.', down_put_path)
    except (putio.PutioError, IndexError):
      down_put_dir = api.File.create_folder(down_put_path)
      if not down_put_dir: return
      log.info('%s folder not found, created.', down_put_path)

  pool = gevent.pool.Pool(size=CFG.io.max)
  downloaded = 0

  try:
    # Find videos sitting in the root folder, and in watched folders.
    items = list_files(kind='video')
  except putio.PutioError:
    items = []

  for folder_name in CFG.watch.putio:
    try:
      folder = list_files(kind='folder', name=folder_name)[0]
      sub_items = get_all_videos(folder.id)
      if not sub_items:
        # Confirm that it's really empty.
        try:
          all_sub_items = list_files(parent=folder.id)
        except putio.PutioError:
          log.info('Removing empty folder from watch folder: %s.', folder_name)
          #folder.delete_item()

      items.extend(sub_items)
    except (putio.PutioError, IndexError):
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

    file_id = hashlib.md5(it.download_url)
    download = Download(file_id, label, it.download_url, file_path, it)
    g = pool.spawn(fetch, download)

  pool.join()
  return len(items)


def watch_transfers():
  """Monitor current put.io transfers and broadcast update events."""
  skip_statuses = ('Seeding', 'Completed')

  known_transfers = {}
  def get_download(transfer):
    if transfer.id in known_transfers:
      return known_transfers[transfer.id], False
    if transfer.status_message in skip_statuses:
      return None, False
    download = Download(transfer.id, transfer.name, '', '', None)
    known_transfers[transfer.id] = download
    return download, True

  while True:
    try:
      if not api: raise TypeError('Continue')
      transfers = api.Transfer.list()
      for transfer in transfers:
        download, new = get_download(transfer)
        if download and transfer.status_message in skip_statuses:
          (download and events.status)(download, 'remove')
          del known_transfers[transfer.id]
          continue

        if not download: continue
        if new: (download and events.init)(download)

        status = str(transfer.status_message).lower()
        if status == 'downloading': status = 'putio-downloading'
        (download and events.status)(download, status)

        if transfer.status_message == 'Downloading':
          (download and events.progress)(download, float(transfer.percent_done),
                                         100.0)

    except (putio.PutioError, TypeError):
      pass

    time.sleep(CFG.poll.transfers)

def main():
  minutes = CFG.poll.downloads/60
  gevent.spawn(convert_worker)

  while True:
    try:
      if (CFG.putio.access_token) and fetch_new():
        log.info('Fetched new episodes, waiting %d minutes.', minutes)
      else:
        log.info('No new episodes, waiting %d minutes.', minutes)
    except KeyboardInterrupt:
      log.info('Caught ctrl-c, shutting down.')
      break
    except putio.PutioError as pe:
      log.info('put.io reported an error, waiting %d minutes: %s', minutes, pe)

    check_now.wait(CFG.poll.downloads) and check_now.clear()


if __name__ == '__main__':
  main()
