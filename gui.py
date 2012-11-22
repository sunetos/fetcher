#!/usr/bin/env python
# encoding: utf-8

from gevent import monkey; __name__ == '__main__' and monkey.patch_all()
from gui.main import main

main()
