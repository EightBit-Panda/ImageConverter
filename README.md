# Image Converter — Linux test build

This folder contains a Linux-oriented run/build setup for the same Image Converter Python app. The existing Windows installer and Windows build files are intentionally left unchanged.

## Target

Start by testing on Ubuntu 22.04/24.04 or Linux Mint (64-bit). Other Linux distributions may work, but need testing.

## Run from source (Ubuntu / Linux Mint / Debian)

1. Install Python, pip, Tkinter, and venv support:

   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-tk python3-venv build-essential
   ```

2. Extract this folder and open a terminal in it.
3. Recommended: create a virtual environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements-linux.txt
   python image_converter.py
   ```

   Alternatively, `./run_linux.sh` installs the listed Python packages with `pip --user` and launches the app. A virtual environment is preferable on modern Debian-based systems.

## Build an AppImage

Build the AppImage on a Linux computer; Windows PyInstaller output cannot be reused for Linux.

1. Install the system packages above.
2. Install the Python requirements in a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install --upgrade pip
   python -m pip install -r requirements-linux.txt
   ```

3. Install AppImageTool for your Linux architecture and make its `appimagetool` command available in `PATH`. Official project: https://github.com/AppImage/AppImageKit/releases
4. Run:

   ```bash
   chmod +x build_linux_appimage.sh
   ./build_linux_appimage.sh
   ```

5. The script should create `ImageConverter-x86_64.AppImage`.
6. Make it executable and test it:

   ```bash
   chmod +x ImageConverter-x86_64.AppImage
   ./ImageConverter-x86_64.AppImage
   ```

The AppImage script is a first packaging attempt, not a verified release. Build and test it on the intended Linux distribution before sharing it. AppImages may still depend on compatible host system libraries.

## Build it for your friend without a Linux PC (GitHub Actions)

The included GitHub Actions workflow can build a Linux AppImage on GitHub's Ubuntu runner, so you do not need to compile it on your Windows PC. This workflow is an initial packaging setup and the result must still be tested on Linux Mint.

1. Upload/push this project to a GitHub repository, keeping the `.github/workflows/build-linux-appimage.yml` file at the repository root. If you place this folder inside an existing repository, move its `.github` folder to the repository root and adjust the workflow's `working-directory` and paths as needed.
2. On GitHub, open **Actions** and select **Build Linux AppImage**. Choose **Run workflow** if it has not run automatically.
3. When the run finishes successfully, open the run and download the `ImageConverter-Linux-x86_64` artifact.
4. Extract the artifact ZIP and send `ImageConverter-x86_64.AppImage` to your tester.
5. On Linux Mint, the tester may need to right-click the AppImage, open **Properties → Permissions**, and enable **Allow executing file as program**, then double-click it. If it does not launch, test from a terminal to see the error.

GitHub Actions only builds the package; it does not prove the package works on every Linux Mint version. Please test before sharing it as a stable release.

## Features and caveats

The Python GUI and image-processing logic are shared with Windows. Optional drag-and-drop support depends on `tkinterdnd2` and the installed Tk environment. The UI uses Windows' Segoe UI font name in several places; Linux will substitute another available font if Segoe UI is not installed. File formats depend on the installed/bundled Pillow plugins and their native codec support.

SVG support uses `resvg_py`; HEIC/HEIF uses `pillow-heif`; AVIF uses `pillow-avif-plugin`.

## Important

- Do not replace the working Windows build with this Linux test setup.
- Test conversions for JPG, PNG, WebP, AVIF, SVG, HEIC/HEIF and ICO on Linux before calling the Linux build stable.
- Linux builds must be created on Linux; PyInstaller is not a cross-compiler.
