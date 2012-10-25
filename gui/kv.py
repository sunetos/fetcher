#!/usr/bin/env python
# encoding: utf-8

"""Helpers for kv files, mostly for pyinstaller quirks."""

__author__ = 'adam@adamia.com (Adam R. Smith)'

from collections import namedtuple
import os

from gui.font_icons import icons as font_icons

font_awesome_path = os.path.abspath('./gui/data/fontawesome-webfont.ttf')
ColorPair = namedtuple('ColorPair', ('bg', 'fg'))
state_cols  = {
    'pending': ColorPair((0, 0, 0.4), (0, 0, 0.4)),
    'moving': ColorPair((0, 0, 0.4), (0, 0, 0.4)),
    'downloading': ColorPair((0.2, 0.5, 0.4), (0.2, 0.5, 0.6)),
    'putio-downloading': ColorPair((0.15, 0.2, 0.3), (0.15, 0.2, 0.5)),
    'completed': ColorPair((0.33, 1, 0.4), (0.33, 1, 0.4)),
    'failed': ColorPair((0, 1, 0.5), (0, 1, 0.7)),
}


