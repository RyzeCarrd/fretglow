"""Build the Windows app and zip, including dependency notices."""
from pathlib import Path
import importlib.metadata
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--windowed',
    '--onedir', '--name', 'FretGlow', '--collect-all', 'libusb_package',
    '--add-data', 'firmware_assets;firmware_assets',
    '--add-data', 'assets;assets',
    '--collect-data', 'customtkinter', 'fretglow.py'], cwd=root, check=True)
app = root / 'dist' / 'FretGlow'
notices = app / 'licenses'
notices.mkdir(exist_ok=True)
for name in ['pyusb', 'libusb-package', 'Brotli', 'customtkinter', 'darkdetect',
             'importlib_resources', 'pyinstaller', 'Pillow']:
    package = importlib.metadata.distribution(name)
    for relative in package.files or []:
        file = package.locate_file(relative)
        if file.is_file() and any(word in str(relative).lower() for word in ('license', 'copying', 'copyright')):
            shutil.copyfile(file, notices / (name + '-' + file.name))
shutil.copyfile(Path(sys.base_prefix) / 'LICENSE.txt', notices / 'Python-LICENSE.txt')
for file in (root / 'notices').glob('*'):
    shutil.copyfile(file, notices / file.name)
shutil.copyfile(root / 'README.md', app / 'README.md')
shutil.copyfile(root / 'TUTORIAL.md', app / 'TUTORIAL.md')
shutil.make_archive(str(root / 'dist' / 'FretGlow-Windows'), 'zip', root / 'dist', 'FretGlow')
print(app / 'FretGlow.exe')
