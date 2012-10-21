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
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty, ObjectProperty, StringProperty

from setproctitle import setproctitle

import util


ColorPair = namedtuple('ColorSet', ('bg', 'fg'))

state_cols  = {
    'pending': ColorPair((0, 0, 0.5), (0, 0, 0.5)),
    'downloading': ColorPair((0.15, 0.5, 0.4), (0.15, 0.5, 0.6)),
    'finished': ColorPair((0.33, 1, 0.4), (0.33, 1, 0.4)),
}


class Controller(FloatLayout):
  downloads = ObjectProperty()


class ControllerApp(App):
  def build(self):
    return Controller()


class Download(BoxLayout):
  name = StringProperty()
  state = StringProperty()
  ratio = NumericProperty()


if __name__ == '__main__':
  setproctitle('fetcher')

  Config.set('graphics', 'width', '300')
  Config.set('graphics', 'height', '100')

  download = None
  def init(dt):
    global download
    download = Download()
    download.state = 'downloading'
    app.root.downloads.add_widget(download)

  def my_callback(dt):
    if download.ratio < 1.0:
      download.ratio += 0.1
    else:
      download.state = 'finished'
      Clock.schedule_once(download_finished, 0.5)

  def download_finished(dt):
    download.parent.remove_widget(download)

  Clock.schedule_once(init)
  Clock.schedule_interval(my_callback, 1/2.)

  app = ControllerApp()
  #app = InteractiveLauncher(ControllerApp())
  app.run()
