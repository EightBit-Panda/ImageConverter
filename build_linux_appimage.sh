#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

APP_NAME="ImageConverter"
APPDIR="$PWD/AppDir"
DIST_DIR="$PWD/dist/Image Converter"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python 3 is required."
  exit 1
fi
if ! python3 -c 'import tkinter' >/dev/null 2>&1; then
  echo "ERROR: Tkinter is missing. On Ubuntu/Linux Mint/Debian: sudo apt install python3-tk"
  exit 1
fi
if ! command -v appimagetool >/dev/null 2>&1; then
  echo "ERROR: appimagetool was not found in PATH. Install AppImageTool first; see README.md."
  exit 1
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-linux.txt
.venv/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir \
  --name "Image Converter" \
  --collect-all tkinterdnd2 \
  --collect-all resvg_py \
  --collect-all pillow_avif \
  --collect-all pillow_heif \
  image_converter.py

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/icons/hicolor/256x256/apps"
cp -a "$DIST_DIR/." "$APPDIR/usr/bin/"
cp image-converter.png "$APPDIR/usr/share/icons/hicolor/256x256/apps/image-converter.png"
cp image-converter.png "$APPDIR/image-converter.png"

cat > "$APPDIR/AppRun" <<'RUNNER'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/Image Converter" "$@"
RUNNER
chmod +x "$APPDIR/AppRun"

mkdir -p "$APPDIR/usr/share/applications"
cat > "$APPDIR/image-converter.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Image Converter
Comment=Convert images locally on your computer
Exec=AppRun
Icon=image-converter
Categories=Graphics;Utility;
Terminal=false
DESKTOP
cp "$APPDIR/image-converter.desktop" "$APPDIR/usr/share/applications/"

ARCH="$(uname -m)"
if [[ "$ARCH" != "x86_64" ]]; then
  echo "WARNING: This script is intended for x86_64. Current architecture: $ARCH"
fi
ARCH=x86_64 appimagetool "$APPDIR" "$PWD/ImageConverter-x86_64.AppImage"
echo
echo "Created: $PWD/ImageConverter-x86_64.AppImage"
echo "Test the AppImage on a clean Ubuntu/Linux Mint system before publishing it."
