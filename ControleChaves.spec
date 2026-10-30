# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[
        # ✅ REMOVIDO: pyzbar — não estamos usando QR Code
    ],
    datas=[
        ('config.ini', '.'),
        ('config.py', '.'),
        ('assets', 'assets'),
        ('utils', 'utils'),
        ('interface', 'interface'),
        ('controle', 'controle'),
        ('admin', 'admin'),
        ('relatorios', 'relatorios'),
        ('autenticacao', 'autenticacao'),
    ],
    hiddenimports=[
        'psycopg2',
        'psycopg2.extensions',
        'autenticacao',
        'autenticacao.session',
        'autenticacao.session_manager',
        'autenticacao.helpers_autenticacao',
        'utils',
        'utils.utils_bd',
        'utils.utils',
        'utils.utils_log',
        'utils.utils_email',
        'utils.caminhos',
        'utils.ui_colors',
        'utils.validacao',
        'utils.email_service',
        'utils.config_app',
        'controle.movimentacoes',
        'controle.email_envio',
        'admin.utilizadores_tab',
        'admin.admin',
        'admin.log_viewer_tab',
        'relatorios.relatorios_tab',
        # ❌ REMOVIDO: pyzbar, qrcode, cv2 — não utilizados
        'datetime',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.styles',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'reportlab.pdfbase',
        'email',
        'email.mime.multipart',
        'email.mime.text',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pyzbar', 'qrcode', 'cv2',  # ✅ Exclui para reduzir tamanho
    ],
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
    console=False,  # ✅ Sem janela preta
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)