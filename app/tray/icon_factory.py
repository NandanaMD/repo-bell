from __future__ import annotations

from PIL import Image, ImageDraw


def build_tray_icon() -> Image.Image:
    size = 64
    image = Image.new("RGBA", (size, size), (26, 28, 34, 255))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((6, 6, 58, 58), radius=12, fill=(33, 39, 50, 255), outline=(79, 91, 110, 255), width=2)
    draw.ellipse((20, 16, 44, 40), fill=(56, 166, 95, 255))
    draw.rectangle((30, 38, 34, 50), fill=(156, 167, 184, 255))
    return image
