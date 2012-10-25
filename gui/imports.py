#!/usr/bin/env python
# encoding: utf-8

"""Workaround bugs in pyinstaller by manually importing submodules."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

import gevent.core, gevent.select, gevent.subprocess
import kivy.core.image.img_dds, kivy.core.image.img_gif, kivy.core.image.img_pil
