from __future__ import annotations

import logging

from PIL import Image, ImageDraw

from app.utils.paths import icon_path

logger = logging.getLogger(__name__)


def build_tray_icon() -> Image.Image:
    icon_file = icon_path()
    if icon_file.exists():
        try:
            return Image.open(icon_file)
        except OSError as exc:
            logger.warning("Failed to load icon file %s: %s", icon_file, exc)

    size = 64
    image = Image.new("RGBA", (size, size), (26, 28, 34, 255))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((6, 6, 58, 58), radius=12, fill=(33, 39, 50, 255), outline=(79, 91, 110, 255), width=2)
    draw.ellipse((20, 16, 44, 40), fill=(56, 166, 95, 255))
    draw.rectangle((30, 38, 34, 50), fill=(156, 167, 184, 255))
    return image
