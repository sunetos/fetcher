#!/usr/bin/env python
# encoding: utf-8

"""Kivy utilities."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

import functools
import subprocess
import sys

from kivy.uix.widget import Widget

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
