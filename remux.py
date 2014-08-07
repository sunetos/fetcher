#!/usr/bin/env python
# encoding: utf-8

"""Just run the remuxer on all files to migrate to the new dir structure."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from gevent import monkey; __name__ == '__main__' and monkey.patch_all()

import fnmatch
import os

from setproctitle import setproctitle
from fetcher import convert, convert_worker, down_path, gevent, orig_path


if __name__ == '__main__':
  setproctitle('fetcher-remux')

  #os.chdir(down_path)
  for root, dirnames, filenames in os.walk(down_path):
    for filename in fnmatch.filter(filenames, '*.mkv.remuxed'):
      convert(os.path.join(root, filename))

  gevent.spawn(convert_worker).join()
