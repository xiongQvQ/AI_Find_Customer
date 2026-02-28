# App Icons

Place your app icons here before building:

- `icon.icns` — macOS icon (required for macOS build)
- `icon.ico`  — Windows icon (required for Windows build)
- `icon.png`  — 512×512 PNG source (use to generate the above)

## Generate from PNG

```bash
# macOS .icns (requires Xcode)
mkdir icon.iconset
sips -z 16 16     icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32     icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32     icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64     icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128   icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256   icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256   icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512   icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512   icon.png --out icon.iconset/icon_512x512.png
iconutil -c icns icon.iconset -o icon.icns

# Windows .ico (requires ImageMagick)
magick convert icon.png -resize 256x256 icon.ico
```

If no icons are provided, build_backend.sh will build without an icon (functional but plain).
