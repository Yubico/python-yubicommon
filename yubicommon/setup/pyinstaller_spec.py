# -*- mode: python -*-
# -*- encoding: utf-8 -*-

import os
import sys
import json
import errno
from glob import glob

VS_VERSION_INFO = """
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four
    # items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=%(ver_tup)r,
    prodvers=%(ver_tup)r,
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x0,
    # Contains a bitmask that specifies the Boolean attributes
    # of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904E4',
        [StringStruct(u'FileDescription', u'%(name)s'),
        StringStruct(u'FileVersion', u'%(ver_str)s'),
        StringStruct(u'InternalName', u'%(internal_name)s'),
        StringStruct(u'LegalCopyright', u'Copyright © 2015 Yubico'),
        StringStruct(u'OriginalFilename', u'%(exe_name)s'),
        StringStruct(u'ProductName', u'%(name)s'),
        StringStruct(u'ProductVersion', u'%(ver_str)s')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1252])])
  ]
)"""

data = json.loads(os.environ['pyinstaller_data'])
data = dict(map(lambda (k, v): (k, v.encode('ascii') if isinstance(v, unicode) else v), data.items()))

DEBUG = bool(data['debug'])
NAME = data['fullname']

WIN = sys.platform in ['win32', 'cygwin']
OSX = sys.platform in ['darwin']

file_ext = '.exe' if WIN else ''

if WIN:
    icon_ext = 'ico'
elif OSX:
    icon_ext = 'icns'
else:
    icon_ext = 'png'
ICON = os.path.join('resources', '%s.%s' % (data['name'], icon_ext))

if not os.path.isfile(ICON):
    ICON = None

merge = []
for script in [s.encode('ascii') for s in data['scripts']]:
    a_name = script.rsplit('/', 1)[-1]
    a = Analysis(
        [script],
        pathex=[''],
        hiddenimports=[],
        hookspath=None,
        runtime_hooks=None
    )
    merge.append((a, a_name, a_name + file_ext))

MERGE(*merge)

# Read version string
ver_str = data['version']

# Read version information on Windows.
VERSION = None
if WIN:
    VERSION = 'build/file_version_info.txt'

    ver_tup = tuple(map(int, ver_str.split('.')))
    # Windows needs 4-tuple.
    if len(ver_tup) < 4:
        ver_tup += (0,) * (4-len(ver_tup))
    elif len(ver_tup) > 4:
        ver_tup = ver_tup[:4]

    # Write version info.
    with open(VERSION, 'w') as f:
        f.write(VS_VERSION_INFO % {
            'name': NAME,
            'internal_name': data['name'],
            'ver_tup': ver_tup,
            'ver_str': ver_str,
            'exe_name': NAME + file_ext
        })

pyzs = map(lambda m: PYZ(m[0].pure), merge)

exes = []
for (a, _, a_name), pyz in zip(merge, pyzs):
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=True,
              name=a_name,
              debug=DEBUG,
              strip=None,
              upx=True,
              # All but the first executable become console scripts.
              console=DEBUG or len(exes) > 0,
              append_pkg=not OSX,
              version=VERSION,
              icon=ICON)
    exes.append(exe)

    # Sign the executable
    if WIN:
        os.system("signtool.exe sign /t http://timestamp.verisign.com/scripts/timstamp.dll \"%s\"" %
                (exe.name))

collect = []
for (a, _, a_name), exe in zip(merge, exes):
    collect += [exe, a.binaries, a.zipfiles, a.datas]

# DLLs, dylibs and executables should go here.
collect.append([(fn[4:], fn, 'BINARY') for fn in glob('lib/*')])

coll = COLLECT(*collect, strip=None, upx=True, name=NAME)

# Create .app for OSX
if OSX:
    app = BUNDLE(coll,
                 name="%s.app" % NAME,
                 version=ver_str,
                 icon=ICON)

    qt_conf = 'dist/%s.app/Contents/Resources/qt.conf' % NAME
    qt_conf_dir = os.path.dirname(qt_conf)
    try:
        os.makedirs(qt_conf_dir)
    except OSError as e:
        if not (e.errno == errno.EEXIST and os.path.isdir(qt_conf_dir)):
            raise
    with open(qt_conf, 'w') as f:
        f.write('[Path]\nPlugins = plugins')

# Create Windows installer
if WIN:
    installer_cfg = 'resources/win-installer.nsi'
    if os.path.isfile(installer_cfg):
        os.system('makensis.exe -D"VERSION=%s" %s' % (ver_str, installer_cfg))
        installer = "dist/%s-win.exe" % data['ver_name']
        os.system("signtool.exe sign /t http://timestamp.verisign.com/scripts/timstamp.dll \"%s\"" %
                 (installer))
        print "Installer created: %s" % installer
