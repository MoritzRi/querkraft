# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['C:\\Users\\morit\\Documents\\Studium\\_BA\\Querkraft\\querkraft.py'],
    pathex=[],
    binaries=[],
    datas=[('res\\start.ui', 'res'), ('res\\system.ui', 'res'), ('res\\schnitt.ui', 'res'), ('res\\iconFragezeichen.png', 'res'), ('res\\icon.png', 'res'), ('res\\schnitt.png', 'res'), ('res\\system.png', 'res'), ('res\\wkhtmltopdf.exe', 'res'), ('res\\template.html', 'res'), ('res\\output.html', 'res'), ('res\\README.txt', 'res')],
    hiddenimports=[],
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
    name='Balken',
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
    icon=['res\\icon.ico'],
)
