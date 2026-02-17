"""
TickerPulse AI - Desktop Entry Point
Used by PyInstaller for the standalone Windows build.
"""

import sys
import os

# Ensure the parent directory is on sys.path so 'backend.*' imports work
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
    parent_dir = os.path.dirname(base_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from backend.app import create_app
from backend.config import Config

if __name__ == '__main__':
    application = create_app()
    application.run(
        host='127.0.0.1',      # Localhost only (security for desktop)
        port=Config.FLASK_PORT,
        debug=False,
        use_reloader=False,     # Reloader breaks PyInstaller
    )
