#!/usr/bin/env python
# encoding: utf-8

"""Base utilities."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from contextlib import contextmanager
import subprocess
import sys
import time


class AttrDict(dict):
  """A reliable nested dot-notation dict."""
  def __getattr__(self, name):
    if not name in self: raise AttributeError('Key %s not found' % name)
    val = self[name]
    if isinstance(val, dict) and not isinstance(val, AttrDict):
      val = self[name] = AttrDict(val)
    return val
  def __setattr__(self, name, val):
    self[name] = AttrDict(val) if isinstance(val, dict) else val
  def __delattr__(self, name):
    del self[name]
  def copy(self):
    return type(self)(self)


_UNITS = ['B', 'K', 'M', 'G', 'T', 'P', 'E']
def human_size(size):
  """Converts bytes to human readable strings."""
  if isinstance(size, unicode): size = int(size)

  s = float(size)*1.0
  i = 0
  while size >= 1024.00 and i < len(_UNITS):
    i += 1
    size /= 1024.00
  return '%.1f%s' % (size, _UNITS[i])


class memoize(object):
  """Memoize with timeout.

  This has been optimized repeatedly to squeeze out extra performance.
  http://code.activestate.com/recipes/325905/ (r5)
  Modified by Adam R. Smith
  """
  _caches = {}
  _timeouts = {}

  def __init__(self, timeout=0):
    self.timeout = timeout

  def collect(self):
    """Clear cache of results which have timed out"""
    for func in self._caches:
      cache = {}
      for key in self._caches[func]:
        if (self._timeouts[func] <= 0 or
            (time.time() - self._caches[func][key][1]) < self._timeouts[func]):
          cache[key] = self._caches[func][key]
      self._caches[func] = cache

  def __call__(self, f):
    cache = self.cache = self._caches[f] = {}
    timeout = self._timeouts[f] = self.timeout

    def func(*args, **kwargs):
      key = tuple(args)
      if len(kwargs):
        kw = kwargs.items()
        kw.sort()
        key += tuple(kw)

      cached = (key in cache)
      if cached:
        v = cache[key]
        if timeout > 0 and (time.time() - v[1]) > timeout:
          cached = False
      if not cached:
        ts = time.time() if timeout else 0
        v = cache[key] = (f(*args, **kwargs), ts)
      return v[0]
    #func.func_name = f.func_name
    func.__doc__ = f.__doc__

    return func


@contextmanager
def caffeinate():
  """Disable system idle/sleep during a job. Mac-only for now."""
  if sys.platform.startswith('darwin'):
    proc = subprocess.Popen(['caffeinate', '-ms'])
    yield
    proc.kill()
  else:
    yield
