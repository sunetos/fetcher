#!/usr/bin/env python
# encoding: utf-8

"""GUI for fetcher."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from gevent import monkey; __name__ == '__main__' and monkey.patch_all()

import kivy; kivy.require('1.4.2')

from collections import namedtuple
from functools import partial
import json
import os
import yaml

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config, ConfigParser
from kivy.lang import Builder
from kivy.logger import Logger as log
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.settings import Settings
from kivy.properties import NumericProperty, ObjectProperty, StringProperty

import gevent
from setproctitle import setproctitle

import fetcher
from gui.util import browse_path, open_path, is_quit_key
from gui.font_icons import icons as font_icons


ColorPair = namedtuple('ColorPair', ('bg', 'fg'))

font_awesome_path = os.path.abspath('./gui/data/fontawesome-webfont.ttf')
state_cols  = {
    'pending': ColorPair((0, 0, 0.4), (0, 0, 0.4)),
    'moving': ColorPair((0, 0, 0.4), (0, 0, 0.4)),
    'downloading': ColorPair((0.2, 0.5, 0.4), (0.2, 0.5, 0.6)),
    'putio-downloading': ColorPair((0.15, 0.2, 0.3), (0.15, 0.2, 0.5)),
    'completed': ColorPair((0.33, 1, 0.4), (0.33, 1, 0.4)),
    'failed': ColorPair((0, 1, 0.5), (0, 1, 0.7)),
}


class Controller(FloatLayout):
  downloads = ObjectProperty()


class ControllerApp(App):
  title = 'Fetcher'

  def build(self):
    # Can't import Window at the top or it will open early with default config.
    from kivy.core.window import Window
    Window.bind(on_key_down=self.on_key_down)

  def on_key_down(self, src, key, scancode, char, mods):
    from kivy.base import stopTouchApp
    if is_quit_key(char, mods):
      stopTouchApp()
    elif char == ',' and 'meta' in mods:
      self.show_settings()

  def resize(self, width, height):
    from kivy.core.window import Window
    Window.size = (width, height)

  def autosize(self):
    if self.settings: return
    downloads = self.root.downloads.children
    if downloads:
      row_height = downloads[0].height
      new_height = (row_height + self.root.downloads.spacing)*len(downloads)
      self.resize(320, new_height)
    else:
      self.resize(320, 5)

  def build_config(self, config):
    self.settings = None
    config.setdefaults('put.io', {
        'api_key': '',
        'api_secret': '',
        'download_path': '~/Movies/TV Shows',
    })
    with open('gui/settings.yml', 'r') as settings_yaml:
      settings_data = yaml.load(settings_yaml)
    self.settings_json = json.dumps(settings_data)

    api_key = config.get('put.io', 'api_key')
    api_secret = config.get('put.io', 'api_secret')
    if not api_key and api_secret:
      Clock.schedule_once(lambda dt: self.show_settings(), 0)

    Clock.schedule_once(lambda dt: self.apply_config(), 0)


  def apply_config(self):
    fetcher.CFG.putio.api_key = self.config.get('put.io', 'api_key')
    fetcher.CFG.putio.api_secret = self.config.get('put.io', 'api_secret')
    fetcher.CFG.download.local = self.config.get('put.io', 'download_path')
    fetcher.load_api()
    fetcher.check_now.set()

  def show_settings(self):
    self.settings = Settings()
    self.settings.add_json_panel('put.io', self.config, data=self.settings_json)
    self.resize(640, 250)
    self.settings.remove_widget(self.settings.menu)
    self.root.add_widget(self.settings)

    def on_close(wgt):
      self.apply_config()
      self.root.remove_widget(self.settings)
      self.settings = None
      self.autosize()

    self.settings.bind(on_close=on_close)


class DownloadRow(BoxLayout):
  name = StringProperty()
  state = StringProperty()
  ratio = NumericProperty()


class LocalDownloadRow(DownloadRow):
  path = StringProperty()


if __name__ == '__main__':
  setproctitle('fetcher')

  Config.set('graphics', 'resizable', '0')
  Config.set('graphics', 'width', '320')
  Config.set('graphics', 'height', '5')
  Config.set('graphics', 'position', 'custom')
  Config.set('graphics', 'top', '10000')
  Config.set('graphics', 'left', '10000')
  Config.set('graphics', 'maxfps', '20')

  downloads = {}

  def init(download):
    if download.id in downloads: return
    if download.path:
      row = LocalDownloadRow()
      row.browse.bind(on_press=lambda wgt: browse_path(download.path))
      row.play.bind(on_press=lambda wgt: open_path(download.path))
      row.close.bind(on_press=lambda wgt: remove_download(download))
    else:
      row = DownloadRow()
    row.state = 'pending'
    row.name = download.label
    if len(row.name) >= 36:
      row.name = row.name[:36] + u'\u2026'
    row.path = download.path
    app.root.downloads.add_widget(row)
    downloads[download.id] = download, row
    Clock.schedule_once(lambda dt: remove_download(download), 60*60*24)

    app.autosize()

  def remove_download(download):
    download, row = downloads[download.id]
    if row.state != 'completed': return
    row.parent.remove_widget(row)
    del downloads[download.id]
    app.autosize()

  def status(download, status):
    download, row = downloads[download.id]
    row.state = status
    if status == 'remove':
      remove_download(download)
    elif status == 'completed':
      row.close.opacity = 1.0

  def progress(download, size, max_size):
    if not download.id in downloads: return
    download, row = downloads[download.id]
    row.ratio = float(size)/max_size

  fetcher.events.init = init
  fetcher.events.status = status
  fetcher.events.progress = progress
  fetcher.log = log

  app = ControllerApp()
  gevent.spawn(fetcher.main)
  gevent.spawn(fetcher.watch_transfers)
  app.run()
