#!/usr/bin/env python
# encoding: utf-8

"""Base utilities."""

__author__ = 'adam@adamia.com (Adam R. Smith)'


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
