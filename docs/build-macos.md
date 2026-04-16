# Building eBL Photo Stitcher on macOS

This guide builds a standalone `.app` bundle and `.dmg` installer on macOS.
Works on both Apple Silicon (M1/M2/M3) and Intel Macs — the build produces
a native binary for whichever architecture you run it on.

## Prerequisites (one-time setup)

Open **Terminal** and run these commands:

### 1. Install Homebrew (skip if already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After install, follow the "Next steps" printed by Homebrew to add it to your PATH.

### 2. Install system dependencies

```bash
brew install cairo libffi python@3.12
```

### 3. Create a Python virtual environment

```bash
python3.12 -m venv ~/ebl-env
source ~/ebl-env/bin/activate
```

### 4. Install Python dependencies

```bash
pip install --upgrade pip
pip install pyinstaller
pip install opencv-python numpy imageio rawpy piexif pyexiv2
pip install cairosvg cairocffi tinycss2 cssselect2 defusedxml webencodings
pip install rembg onnxruntime
pip install Pillow scikit-image scipy
pip install tqdm requests pandas openpyxl pillow-heif
```

## Build steps

### 1. Clone the repository

```bash
git clone https://github.com/ludovicus-hispanicus/ebl-photo-stitcher.git
cd ebl-photo-stitcher
git checkout v2.0-project-config
```

### 2. Activate the virtual environment (if not already active)

```bash
source ~/ebl-env/bin/activate
```

### 3. Build the `.app` bundle

```bash
python -m PyInstaller eBL_Photo_Stitcher_MacOS.spec --noconfirm
```

This creates `dist/eBL Photo Stitcher.app` (takes 3-10 minutes).

### 4. Sign the app (ad-hoc signature, required for macOS)

```bash
codesign --remove-signature "dist/eBL Photo Stitcher.app" 2>/dev/null || true
codesign --force --deep --sign - "dist/eBL Photo Stitcher.app"
codesign --verify --verbose "dist/eBL Photo Stitcher.app"
```

### 5. Create the DMG installer

```bash
hdiutil create -volname "eBL Photo Stitcher" \
  -srcfolder "dist/eBL Photo Stitcher.app" \
  -ov -format UDZO \
  "dist/eBL_Photo_Stitcher_macOS.dmg"
```

The DMG will be at `dist/eBL_Photo_Stitcher_macOS.dmg`.

## Installation

1. Double-click the DMG to mount it
2. Drag `eBL Photo Stitcher.app` to `/Applications`
3. If macOS blocks the app on first launch, run:

```bash
xattr -cr "/Applications/eBL Photo Stitcher.app"
```

Then open normally from the Applications folder.

## First run

On first run, the app needs to download the U2NET AI model (~176MB) used
for background removal. This happens automatically. If the download fails
due to firewall issues, download it manually:

1. Download: https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx
2. Save to: `~/.u2net/u2net.onnx` (create the `.u2net` folder if needed)

In Finder, use **Cmd+Shift+G** and type `~/.u2net` to navigate there.

## Troubleshooting

**"App can't be opened because it's from an unidentified developer"**
→ Run `xattr -cr "/Applications/eBL Photo Stitcher.app"` in Terminal.

**"python3.12: command not found"**
→ Run `brew install python@3.12` again and make sure brew is in your PATH.

**Build fails with "libcairo not found"**
→ Run `brew install cairo` and retry.

**"Module not found" errors at runtime**
→ Make sure you activated the virtual environment before building:
  `source ~/ebl-env/bin/activate`
