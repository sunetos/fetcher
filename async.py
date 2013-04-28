#!/usr/bin/env python
# encoding: utf-8

"""Async/greenlet utilites."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from contextlib import contextmanager
from functools import partial
import time

import gevent


def set_interval(func, delay, now=False, *args, **kwargs):
  """Similar to javascript's setInterval but for gevent, and in seconds."""
  def run():
    run_again = True
    if now: run_again = func(*args, **kwargs)
    while run_again is not False:
      time.sleep(delay)
      run_again = func(*args, **kwargs)
  return gevent.spawn(run)

@contextmanager
def green_block(func, *args, **kwargs):
  """Context manager to kill a greenlet when finished."""
  g = gevent.spawn(func, *args, **kwargs)
  yield
  g.kill()

interval_block = partial(green_block, set_interval)
