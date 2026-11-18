# -*- mode: python ; coding: utf-8 -*-
# Gera dist\ResetAlmofadasEpson.exe  (executar: GERAR_EXE.bat)
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hidden = [m for m in collect_submodules('epson_usb')
          if not m.startswith('epson_usb.tests')]
hidden += ['epson_print_conf', 'epson_usb_bridge']
hidden += collect_submodules('pysnmp') + collect_submodules('pyasn1')

a = Analysis(
    ['reset_almofadas.py'],
    pathex=['motor'],
    datas=collect_data_files('pysnmp'),
    hiddenimports=hidden,
    excludes=['tkinter', 'black', 'blib2to3'],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name='ResetAlmofadasEpson',
    console=True,
    upx=False,
)
