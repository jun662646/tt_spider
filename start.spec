# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['start.py',
        'tt_spider/spiders/tt.py',
        'tt_spider/spiders/__init__.py',
        'tt_spider/items.py',
        'tt_spider/__init__.py',
        'tt_spider/middlewares.py',
        'tt_spider/pipelines.py',
        'tt_spider/settings.py',
    ],
    pathex=[],
    binaries=[],
    datas=[('scrapy.cfg','.')],
    hiddenimports=[
        'pandas',
        'selenium',
        'scrapy',
        'tt_spider.settings',
        'tt_spider.spiders',
        'tt_spider.middlewares',
        'tt_spider.pipelines',
        'tt_spider.items',
        'tt_spider.spiders.tt',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='tt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='tt256.ico'
)
