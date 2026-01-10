from PIL import Image
from pathlib import Path

def get_thumbnail(original_path, size=(400, 400)):
    thumb_dir = original_path.parent / ".thumbs"
    thumb_dir.mkdir(exist_ok=True)

    thumb_path = thumb_dir / original_path.name

    if not thumb_path.exists():
        img = Image.open(original_path)
        img.thumbnail(size)
        img.save(thumb_path, optimize=True, quality=70)

    return thumb_path
