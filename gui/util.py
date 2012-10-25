#!/usr/bin/env python
# encoding: utf-8

"""Kivy utilities."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

import ctypes
import functools
import os
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

def get_free_space(path):
  """ Return folder/drive free space (in bytes) """
  path = os.path.expanduser(path)
  if sys.platform == 'win32':
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(path), None,
                                               None, ctypes.pointer(free_bytes))
    return free_bytes.value
  else:
    stat = os.statvfs(path)
    return stat.f_bavail*stat.f_frsize
