#!/bin/bash

rm -rf gui/dist build/ gui/build/
python gui/extern/pyinstaller/pyinstaller.py gui/fetcher.spec
pushd gui/dist
mv Fetcher.app/.Python Fetcher.app/Python
hdiutil create Fetcher.dmg -srcfolder Fetcher.app -ov
popd
