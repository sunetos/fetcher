#!/usr/bin/env python
# encoding: utf-8

"""Kivy utilities."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

import functools
import subprocess
import sys

from kivy.uix.widget import Widget

def add_ids_to_widgets():
  """Monkey-patch the widget class to add attributes for each child by id."""
  old_add_widget = Widget.add_widget
  old_remove_widget = Widget.remove_widget

  @functools.wraps(old_add_widget)
  def add_widget(self, widget, *args, **kwargs):
    #import logging as log; log.info('in add_widget')
    ret = old_add_widget(self, widget, *args, **kwargs)
    print self, widget, hasattr(widget, 'id'), getattr(widget, 'id')
    if widget.id:
      print widget.id
      assert(not hasattr(self, widget.id))
      setattr(self, widget.id, widget)
    return ret

  @functools.wraps(old_remove_widget)
  def remove_widget(self, widget, *args, **kwargs):
    print self, widget
    ret = old_remove_widget(self, widget, *args, **kwargs)
    if widget.id and hasattr(self, widget.id):
      delattr(self, widget.id)
    return ret

  Widget.add_widget = add_widget
  Widget.remove_widget = remove_widget

def browse_path(path):
  """Open a platform-specific file browser to the given path."""
  if sys.platform == 'darwin':
    subprocess.call(['open', '-R', path])
  elif sys.platform == 'win32':
    subprocess.call(['explorer', path])

def open_path(path):
  """Open a file in the default platform-specific handler."""
  if sys.platform == 'darwin':
    subprocess.call(['open', path])
  elif sys.platform == 'win32':
    subprocess.call(['start', path])

def is_quit_key(char, mods):
  """See if this keypress is a quit command on the current OS."""
  if sys.platform == 'darwin':
    return char in ('w', 'q') and 'meta' in mods
