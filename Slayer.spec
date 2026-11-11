# How build_exe.bat packs the window version (main.py) into Slayer.exe, using PyInstaller.
# The result is the folder dist/Slayer: Slayer.exe plus an _internal folder holding Python, pygame,
# the CSVs and the fonts. The whole folder has to travel together; Slayer.exe alone won't run.
from pathlib import Path

game = Path(SPECPATH)  # the folder this file is in

# Every Slayer_*.py, named outright. Some are imported inside functions, and this makes sure none get left out.
slayer_modules = sorted(path.stem for path in game.glob('Slayer_*.py'))

a = Analysis(
    [str(game / 'main.py')],
    pathex=[str(game)],
    datas=[
        (str(game / 'supporting_docs' / '*.csv'), 'supporting_docs'),
        (str(game / 'assets'), 'assets'),  # fonts (with their licenses, which have to ship with them) and sprites
    ],
    hiddenimports=slayer_modules,
    # Things the game never uses, to keep the folder smaller. numpy is the big one: pygame only uses it
    # for optional extras (surfarray/sndarray) that Slayer doesn't touch.
    excludes=['tkinter', 'unittest', 'pydoc', 'check_data', 'numpy', 'psutil', 'charset_normalizer'],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Slayer',
    console=False,  # just the game window, no black command-prompt window behind it
    upx=False,      # UPX packing tends to make antivirus programs suspicious, so it's off
)

coll = COLLECT(exe, a.binaries, a.datas, name='Slayer', upx=False)
