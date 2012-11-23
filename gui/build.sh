#!/bin/bash

rm -rf dist build
python setup.py py2app --site-packages --packages=kivy,gui &&
rm dist/Fetcher.app/Contents/Resources/gui/controller.ini
pushd dist &&
hdiutil create Fetcher.dmg -srcfolder Fetcher.app -ov &&
popd &&
mv dist/Fetcher.dmg .
