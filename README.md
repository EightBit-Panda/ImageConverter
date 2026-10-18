# Image Converter

Image Converter is a desktop application for converting images between multiple file formats. It uses Python and Tkinter and supports Windows and Linux.

## Windows

Two versions are available:

- **Windows Installer** — installs Image Converter on your PC, creates shortcuts, and supports uninstalling through Windows Settings.
- **Standalone EXE** — runs without a separate installation.

## Linux

Linux support is available for testing on 64-bit Ubuntu and Linux Mint.

- Run the application from source using Python.
- Build an AppImage using the included Linux build script or GitHub Actions workflow.

The Linux package is still experimental and needs testing on the intended Linux distribution before it can be considered a stable release.

## Features

- Convert images between supported formats.
- Simple graphical user interface.
- Optional drag-and-drop support.
- Support for formats including JPG, PNG, WebP, AVIF, SVG, HEIC/HEIF and ICO, subject to platform dependencies and codec support.

## Downloads

Download the Windows versions from the project's GitHub Releases or Actions artifacts. Linux builds are available through the Linux build workflow while testing continues.

## Development

The Windows and Linux builds share the same Python application source, with platform-specific packaging and dependencies.

See the repository files for installation instructions, dependencies and build scripts.
