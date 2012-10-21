#!/usr/bin/env python
# encoding: utf-8

"""GUI for fetcher."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from gevent import monkey; __name__ == '__main__' and monkey.patch_all()

import kivy; kivy.require('1.4.2')

from collections import namedtuple
from functools import partial

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.interactive import InteractiveLauncher
from kivy.lang import Builder
from kivy.logger import Logger as log
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty, ObjectProperty, StringProperty

import gevent
from setproctitle import setproctitle

import fetcher
import gui.util


ColorPair = namedtuple('ColorPair', ('bg', 'fg'))

state_cols  = {
    'pending': ColorPair((0, 0, 0.5), (0, 0, 0.5)),
    'moving': ColorPair((0, 0, 0.5), (0, 0, 0.5)),
    'downloading': ColorPair((0.15, 0.5, 0.4), (0.15, 0.5, 0.6)),
    'complete': ColorPair((0.33, 1, 0.4), (0.33, 1, 0.4)),
    'failed': ColorPair((0, 1, 0.5), (0, 1, 0.7)),
}


class Controller(FloatLayout):
  downloads = ObjectProperty()


class ControllerApp(App): pass


class DownloadRow(BoxLayout):
  name = StringProperty()
  state = StringProperty()
  ratio = NumericProperty()


if __name__ == '__main__':
  setproctitle('fetcher')

  Config.set('graphics', 'width', '300')
  Config.set('graphics', 'height', '30')

  downloads = {}

  def init(download):
    row = DownloadRow()
    row.state = 'pending'
    row.name = download.label
    app.root.downloads.add_widget(row)
    downloads[download.id] = download, row
    Config.set('graphics', 'height', str(30 + row.height*len(downloads)))

  def status(download, status):
    download, row = downloads[download.id]
    row.state = status

  def progress(download, size, max_size):
    download, row = downloads[download.id]
    row.ratio = float(size)/max_size

  fetcher.events.init = init
  fetcher.events.status = status
  fetcher.events.progress = progress
  fetcher.log = log

  #app = InteractiveLauncher(ControllerApp())
  #app.run()
  app = ControllerApp()
  gevent.spawn(fetcher.main)
  app.run()
