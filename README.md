# Mouse Odometer

IMPORTS for python:
pip install pywin32
pip install winotify
pip install pystray
pip install pyinstaller

For build 
pyinstaller --onefile --windowed --icon=favicon.ico --hidden-import=win32gui --hidden-import=win32api --add-data "favicon.ico;." main.py 
