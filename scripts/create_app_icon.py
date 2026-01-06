#!/usr/bin/env python3
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/create_app_icon.py
# Description: Creates a custom app icon for MyRAGDB macOS app
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-06

import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

def create_icon(resources_dir):
    """Create macOS app icon with magnifying glass design."""

    # Create iconset directory
    iconset_dir = Path(resources_dir) / "AppIcon.iconset"
    iconset_dir.mkdir(parents=True, exist_ok=True)

    # Icon sizes required for macOS
    sizes = [16, 32, 64, 128, 256, 512, 1024]

    print(f"🎨 Creating app icon...")

    for size in sizes:
        # Create base image with dark blue gradient background
        img = Image.new('RGB', (size, size), color='#0f172a')
        draw = ImageDraw.Draw(img)

        # Draw gradient background (dark blue to slightly lighter blue)
        for y in range(size):
            # Gradient from dark slate (#0f172a) to slate (#1e293b)
            ratio = y / size
            r = int(15 + (30 - 15) * ratio)
            g = int(23 + (41 - 23) * ratio)
            b = int(42 + (59 - 42) * ratio)
            draw.rectangle([(0, y), (size, y+1)], fill=(r, g, b))

        # Draw magnifying glass for larger icons
        if size >= 32:
            # Scale factor for all elements
            scale = size / 512

            # Magnifying glass parameters
            circle_radius = int(140 * scale)
            circle_center = (int(size * 0.42), int(size * 0.42))
            circle_width = max(2, int(24 * scale))

            # Draw glass circle (light blue)
            draw.ellipse([
                circle_center[0] - circle_radius,
                circle_center[1] - circle_radius,
                circle_center[0] + circle_radius,
                circle_center[1] + circle_radius
            ], outline='#60a5fa', width=circle_width)

            # Draw inner glow effect
            if size >= 128:
                inner_radius = circle_radius - int(12 * scale)
                draw.ellipse([
                    circle_center[0] - inner_radius,
                    circle_center[1] - inner_radius,
                    circle_center[0] + inner_radius,
                    circle_center[1] + inner_radius
                ], outline='#93c5fd', width=max(1, int(8 * scale)))

            # Draw handle
            handle_width = circle_width
            handle_start_x = circle_center[0] + int(circle_radius * 0.65)
            handle_start_y = circle_center[1] + int(circle_radius * 0.65)
            handle_end_x = int(size * 0.78)
            handle_end_y = int(size * 0.78)

            # Draw handle with rounded cap effect
            draw.line([
                (handle_start_x, handle_start_y),
                (handle_end_x, handle_end_y)
            ], fill='#60a5fa', width=handle_width)

            # Add handle end cap (circle)
            cap_radius = handle_width // 2
            draw.ellipse([
                handle_end_x - cap_radius,
                handle_end_y - cap_radius,
                handle_end_x + cap_radius,
                handle_end_y + cap_radius
            ], fill='#60a5fa')

            # Add subtle "DB" text inside magnifying glass for large icons
            if size >= 256:
                try:
                    # Try to use a system font
                    font_size = int(80 * scale)
                    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", font_size)
                except:
                    font = ImageFont.load_default()

                # Draw "DB" text
                text = "DB"
                # Get text bounding box
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                text_x = circle_center[0] - text_width // 2
                text_y = circle_center[1] - text_height // 2 - int(10 * scale)

                draw.text((text_x, text_y), text, fill='#60a5fa', font=font)

        # Save standard resolution
        img.save(iconset_dir / f"icon_{size}x{size}.png")

        # Save @2x resolution (for Retina displays)
        if size <= 512:
            img_2x = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            img_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")

        print(f"  ✓ Created {size}x{size} icon")

    return iconset_dir

def main():
    # Get resources directory from command line or default
    if len(sys.argv) > 1:
        resources_dir = sys.argv[1]
    else:
        # Default to MyRAGDB.app/Contents/Resources
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        resources_dir = project_root / "MyRAGDB.app" / "Contents" / "Resources"

    iconset_dir = create_icon(resources_dir)
    print(f"\n✅ Icon images created in {iconset_dir}")
    print(f"\n🔄 Converting to .icns format...")

    # Convert to icns using iconutil (macOS built-in tool)
    icns_path = Path(resources_dir) / "AppIcon.icns"
    os.system(f'iconutil -c icns "{iconset_dir}" -o "{icns_path}"')

    # Clean up iconset directory
    import shutil
    shutil.rmtree(iconset_dir)

    print(f"✅ App icon created: {icns_path}")

if __name__ == "__main__":
    main()
