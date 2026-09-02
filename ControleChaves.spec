# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
    ('C:\\\\Users\\\\nilo.alvira\\\\AppData\\\\Roaming\\\\Python\\\\Python313\\\\site-packages\\\\pyzbar\\\\libiconv.dll', 'pyzbar'),
    ('C:\\\\Users\\\\nilo.alvira\\\\AppData\\\\Roaming\\\\Python\\\\Python313\\\\site-packages\\\\pyzbar\\\\libzbar-64.dll', 'pyzbar'),
],
    datas=[
        ('config.ini', '.'),
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'psycopg2',
        'psycopg2.extensions',
        'autenticacao',
        'autenticacao.session',
        'utils',
        'pyzbar',
        'pyzbar.pyzbar',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ControleChaves',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)