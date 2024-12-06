# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew

a = Analysis(
    ['.\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon/*.png', 'icon'),     # アイコンファイル
        ('icon/*.gif', 'icon'),     # GIFアニメーション
        ('font/*.ttf', 'font'),     # フォントファイル
        ('*.kv', '.'),              # Kivyのレイアウトファイル
        ('site_configs.json', '.'), # サイト設定ファイル
        ('msx0reup_settings.ini', '.'), # アプリケーション設定ファイル

    ],
    hiddenimports=[
        'win32api',
        'win32con',
        'win32gui',
        'pkg_resources.py2_warn',
        'kivy',
        'kivy.core.window._window_sdl2',
        'kivy.core.text',
        'kivy.core.text.text_sdl2',
        'kivy.core.text.markup',
        'kivy.core.image',
        'certifi',
        'requests',
        'chardet',
        'lhafile',
        'html2text',
        'logging.handlers',
        'logging.config',
        'win32timezone', 
        'pytz',
        'tzdata',
        'asyncio', 

    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['jnius', 'android'],  # Android関連のモジュールを除外
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
Key = ['mkl']

def remove_from_list(input, keys):
    outlist = []
    for item in input:
        name, _, _ = item
        flag = 0
        for key_word in keys:
            if name.find(key_word) > -1:
                flag = 1
        if flag != 1:
            outlist.append(item)
    return outlist

a.binaries = remove_from_list(a.binaries, Key)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
     *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],  # Kivy binaries excluding gstreamer.dep_bins
     [],
    name='msx0reup',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
