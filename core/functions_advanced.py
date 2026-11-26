"""Media helpers behind the agent's `media` tool (optional dependencies)."""

from pathlib import Path


def image_info(path: str) -> dict:
    """Get image information."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            return {"path": path, "format": img.format, "size": img.size, "width": img.width, "height": img.height}
    except Exception as e:
        return {"error": str(e)}


def image_resize(path: str, width: int, height: int) -> dict:
    """Resize image."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            img.thumbnail((width, height))
            p = Path(path)
            new = str(p.with_name(f"{p.stem}_resized{p.suffix}"))
            img.save(new)
            return {"saved": new}
    except Exception as e:
        return {"error": str(e)}


def image_thumbnail(path: str, size: int = 128) -> dict:
    """Create thumbnail."""
    try:
        from PIL import Image
        with Image.open(path) as img:
            img.thumbnail((size, size))
            p = Path(path)
            new = str(p.with_name(f"{p.stem}_thumb{p.suffix}"))
            img.save(new)
            return {"saved": new}
    except Exception as e:
        return {"error": str(e)}


def pdf_info(path: str) -> dict:
    """Get PDF info."""
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return {"path": path, "pages": len(reader.pages)}
    except Exception as e:
        return {"error": str(e)}


def qr_code(text: str, path: str = None) -> dict:
    """Generate QR code."""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        filename = path or "qrcode.png"
        img.save(filename)
        return {"saved": filename}
    except Exception as e:
        return {"error": str(e)}
