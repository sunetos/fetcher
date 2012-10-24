#!/bin/bash

python gui/extern/pyinstaller/pyinstaller.py --name Fetcher gui/main.py
mv Fetcher.spec gui/fetcher.spec
