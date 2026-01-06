#!/bin/bash
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/create_macos_app.sh
# Description: Creates a macOS .app bundle for MyRAGDB with custom icon
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-06

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Creating MyRAGDB.app for macOS...${NC}"

# Get the script directory (myragdb root)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Define app bundle structure
APP_NAME="MyRAGDB"
APP_BUNDLE="${PROJECT_ROOT}/${APP_NAME}.app"
APP_CONTENTS="${APP_BUNDLE}/Contents"
APP_MACOS="${APP_CONTENTS}/MacOS"
APP_RESOURCES="${APP_CONTENTS}/Resources"

echo -e "${YELLOW}📁 Creating app bundle structure...${NC}"

# Remove existing app if it exists
if [ -d "$APP_BUNDLE" ]; then
    echo -e "${YELLOW}⚠️  Removing existing ${APP_NAME}.app...${NC}"
    rm -rf "$APP_BUNDLE"
fi

# Create directory structure
mkdir -p "$APP_MACOS"
mkdir -p "$APP_RESOURCES"

# Create Info.plist
echo -e "${YELLOW}📝 Creating Info.plist...${NC}"
cat > "$APP_CONTENTS/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>MyRAGDB</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.arionetworks.myragdb</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>MyRAGDB</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>2.28.1</string>
    <key>CFBundleVersion</key>
    <string>2026.01.06.2.28.1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF

# Create launcher script
echo -e "${YELLOW}📝 Creating launcher script...${NC}"
cat > "$APP_MACOS/${APP_NAME}" << 'EOF'
#!/bin/bash
# MyRAGDB Launcher Script

# Get the directory where this app bundle is located
APP_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_BUNDLE="$(dirname "$(dirname "$APP_PATH")")"
PROJECT_ROOT="$(dirname "$APP_BUNDLE")"

# Create a wrapper script for Terminal
WRAPPER_SCRIPT="/tmp/myragdb_launcher_$$.sh"
cat > "$WRAPPER_SCRIPT" << 'WRAPPER_EOF'
#!/bin/bash

# Get project root from arguments
PROJECT_ROOT="$1"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Trap signals to run stop.sh when terminal is closed
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down MyRAGDB services...${NC}"
    "$PROJECT_ROOT/stop.sh"
    exit 0
}

trap cleanup SIGTERM SIGINT SIGHUP EXIT

# Run the startup script
./start.sh

# Show status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  MyRAGDB is now running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  • Meilisearch:     http://localhost:7700"
echo -e "  • MyRAGDB API:     http://localhost:3003"
echo -e "  • MCP Middleware:  http://localhost:8093"
echo -e "  • Web UI:          http://localhost:3003"
echo ""
echo -e "${YELLOW}To stop: Close this window or press Ctrl+C${NC}"
echo ""

# Keep the terminal open and monitor services
while true; do
    sleep 2
    # Check if any of the services are still running
    if [ ! -f "$PROJECT_ROOT/.server.pid" ] && [ ! -f "$PROJECT_ROOT/.middleware.pid" ]; then
        echo -e "${RED}All services stopped. Closing...${NC}"
        sleep 2
        exit 0
    fi
done
WRAPPER_EOF

chmod +x "$WRAPPER_SCRIPT"

# Open Terminal with the wrapper script
osascript <<APPLESCRIPT
tell application "Terminal"
    activate
    do script "$WRAPPER_SCRIPT \"$PROJECT_ROOT\""
end tell
APPLESCRIPT

# Clean up wrapper script after a delay
(sleep 5 && rm -f "$WRAPPER_SCRIPT") &
EOF

# Make launcher executable
chmod +x "$APP_MACOS/${APP_NAME}"

# Create app icon using SF Symbols or emoji fallback
echo -e "${YELLOW}🎨 Creating app icon...${NC}"

# Try to create icon using Python (if available)
if command -v python3 &> /dev/null; then
    python3 << 'PYTHON_SCRIPT'
import os
from pathlib import Path

# Create a simple icon using ImageMagick or Python PIL if available
try:
    from PIL import Image, ImageDraw, ImageFont

    # Create base icon sizes for macOS
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    # Get resources directory from environment
    resources_dir = os.environ.get('APP_RESOURCES', './MyRAGDB.app/Contents/Resources')
    iconset_dir = f"{resources_dir}/AppIcon.iconset"
    os.makedirs(iconset_dir, exist_ok=True)

    for size in sizes:
        # Create image with gradient background
        img = Image.new('RGB', (size, size), color='#1e293b')
        draw = ImageDraw.Draw(img)

        # Draw a gradient-like effect
        for i in range(size):
            alpha = int(255 * (i / size))
            draw.rectangle([(0, i), (size, i+1)], fill=(30, 41, 59))

        # Draw search icon (magnifying glass) using circles and rectangles
        if size >= 64:
            # Scale factor
            scale = size / 512

            # Magnifying glass circle
            circle_radius = int(120 * scale)
            circle_center = (int(size * 0.4), int(size * 0.4))
            circle_width = int(20 * scale)

            # Draw outer circle
            draw.ellipse([
                circle_center[0] - circle_radius,
                circle_center[1] - circle_radius,
                circle_center[0] + circle_radius,
                circle_center[1] + circle_radius
            ], outline='#60a5fa', width=circle_width)

            # Draw handle
            handle_start = (circle_center[0] + int(circle_radius * 0.7),
                          circle_center[1] + int(circle_radius * 0.7))
            handle_end = (int(size * 0.8), int(size * 0.8))
            draw.line([handle_start, handle_end], fill='#60a5fa', width=circle_width)

        # Save standard resolution
        img.save(f"{iconset_dir}/icon_{size}x{size}.png")

        # Save @2x resolution
        if size <= 512:
            img_2x = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            img_2x.save(f"{iconset_dir}/icon_{size}x{size}@2x.png")

    print(f"✓ Created icon images in {iconset_dir}")

except ImportError:
    print("⚠️  PIL not available, skipping icon creation")
    print("   Install with: pip install Pillow")
except Exception as e:
    print(f"⚠️  Error creating icon: {e}")
PYTHON_SCRIPT
else
    echo -e "${YELLOW}⚠️  Python3 not available, using fallback icon${NC}"
fi

# Convert iconset to icns using iconutil (macOS built-in)
if [ -d "$APP_RESOURCES/AppIcon.iconset" ]; then
    echo -e "${YELLOW}🔄 Converting iconset to icns...${NC}"
    iconutil -c icns "$APP_RESOURCES/AppIcon.iconset" -o "$APP_RESOURCES/AppIcon.icns"
    rm -rf "$APP_RESOURCES/AppIcon.iconset"
    echo -e "${GREEN}✓ App icon created${NC}"
else
    echo -e "${YELLOW}⚠️  No iconset created, app will use default icon${NC}"
fi

echo ""
echo -e "${GREEN}✅ ${APP_NAME}.app created successfully!${NC}"
echo ""
echo -e "${BLUE}📍 Location: ${APP_BUNDLE}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Drag ${APP_NAME}.app to your Applications folder (optional)"
echo -e "  2. Drag ${APP_NAME}.app to your Dock for quick access"
echo -e "  3. Double-click to launch MyRAGDB services"
echo ""
echo -e "${BLUE}To open now:${NC}"
echo -e "  open \"${APP_BUNDLE}\""
echo ""
echo -e "${YELLOW}Note:${NC} To stop services, run: ./stop.sh"
echo -e "      Or quit the app from the Dock/Activity Monitor"
