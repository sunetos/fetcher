#!/usr/bin/env python
# encoding: utf-8

"""GUI for fetcher."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from gevent import monkey; __name__ == '__main__' and monkey.patch_all()

import kivy; kivy.require('1.4.2')

from collections import namedtuple
from functools import partial
import os

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.lang import Builder
from kivy.logger import Logger as log
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty, ObjectProperty, StringProperty

import gevent
from setproctitle import setproctitle

import fetcher
from gui.util import browse_path, open_path, is_quit_key
from gui.font_awesome_to_png import icons as font_icons


ColorPair = namedtuple('ColorPair', ('bg', 'fg'))

font_awesome_path = os.path.abspath('./gui/data/fontawesome-webfont.ttf')
state_cols  = {
    'pending': ColorPair((0, 0, 0.5), (0, 0, 0.5)),
    'moving': ColorPair((0, 0, 0.5), (0, 0, 0.5)),
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


class DownloadRow(BoxLayout):
  name = StringProperty()
  state = StringProperty()
  ratio = NumericProperty()


class LocalDownloadRow(DownloadRow):
  path = StringProperty()


if __name__ == '__main__':
  setproctitle('fetcher')

  Config.set('graphics', 'width', '300')
  Config.set('graphics', 'height', '5')
  Config.set('graphics', 'position', 'custom')
  Config.set('graphics', 'top', '10000')
  Config.set('graphics', 'left', '10000')
  Config.set('graphics', 'maxfps', '30')

  downloads = {}

  def autosize():
    from kivy.core.window import Window
    if app.root.downloads.children:
      row_height = app.root.downloads.children[0].height
      new_height = (row_height + app.root.downloads.spacing)*len(downloads)
      Window.size = (300, new_height)
    else:
      Window.size = (300, 5)

  def init(download):
    if download.id in downloads: return
    if download.path:
      row = LocalDownloadRow()
      row.browse.bind(on_press=lambda wgt: browse_path(download.path))
      row.play.bind(on_press=lambda wgt: open_path(download.path))
    else:
      row = DownloadRow()
    row.state = 'pending'
    row.name = download.label
    if len(row.name) >= 36:
      row.name = row.name[:36] + u'\u2026'
    row.path = download.path
    app.root.downloads.add_widget(row)
    downloads[download.id] = download, row

    autosize()

  def status(download, status):
    download, row = downloads[download.id]
    row.state = status
    if status == 'remove':
      row.parent.remove_widget(row)
      del downloads[download.id]
      autosize()

  def progress(download, size, max_size):
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
