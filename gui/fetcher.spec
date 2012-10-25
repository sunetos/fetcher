# -*- mode: python -*-
from kivy.tools.packaging.pyinstaller_hooks import install_hooks
install_hooks(globals())

a = Analysis(['gui/main.py'],
             pathex=['/Users/adam/Documents/Projects/fetcher'],
             hiddenimports=[])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build/pyi.darwin/Fetcher', 'Fetcher'),
          debug=False,
          strip=None,
          upx=True,
          console=True )
coll = COLLECT(exe, Tree('.'),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist', 'Fetcher.app'))
