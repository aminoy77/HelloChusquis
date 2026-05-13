"""Advanced built-in functions (dependencies optional)."""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path


def try_import_image():
    """Try to import image-related libraries."""
    try:
        from PIL import Image
        return True
    except Exception:
        return False


def try_import_pdf():
    """Try to import PDF libraries."""
    try:
        import PyPDF2
        return True
    except Exception:
        return False


def try_import_qr():
    """Try to import QR libraries."""
    try:
        import qrcode
        return True
    except Exception:
        return False


def try_import_barcode():
    """Try to import barcode libraries."""
    try:
        import pyzbar
        return True
    except Exception:
        return False


def image_info(path: str) -> dict:
    """Get image information."""
    if not try_import_image():
        return {"error": "PIL not installed"}
    try:
        from PIL import Image
        with Image.open(path) as img:
            return {"path": path, "format": img.format, "size": img.size, "width": img.width, "height": img.height}
    except Exception as e:
        return {"error": str(e)}


def image_resize(path: str, width: int, height: int) -> dict:
    """Resize image."""
    if not try_import_image():
        return {"error": "PIL not installed"}
    try:
        from PIL import Image
        with Image.open(path) as img:
            img.thumbnail((width, height))
            new = path.replace(".", "_resized.")
            img.save(new)
            return {"saved": new}
    except Exception as e:
        return {"error": str(e)}


def image_thumbnail(path: str, size: int = 128) -> dict:
    """Create thumbnail."""
    if not try_import_image():
        return {"error": "PIL not installed"}
    try:
        from PIL import Image
        with Image.open(path) as img:
            img.thumbnail((size, size))
            new = path.replace(".", "_thumb.")
            img.save(new)
            return {"saved": new}
    except Exception as e:
        return {"error": str(e)}


def pdf_info(path: str) -> dict:
    """Get PDF info."""
    if not try_import_pdf():
        return {"error": "PyPDF2 not installed"}
    try:
        import PyPDF2
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return {"path": path, "pages": len(reader.pages)}
    except Exception as e:
        return {"error": str(e)}


def csv_to_json(path: str) -> dict:
    """Convert CSV to JSON."""
    import csv
    try:
        with open(path) as f:
            reader = csv.DictReader(f)
            data = list(reader)
            return {"json": json.dumps(data, indent=2), "rows": len(data)}
    except Exception as e:
        return {"error": str(e)}


def download_file(url: str, path: str = None) -> dict:
    """Download file."""
    import httpx
    try:
        r = httpx.get(url, timeout=60)
        filename = path or Path(url).name
        with open(filename, "wb") as f:
            f.write(r.content)
        return {"saved": filename, "size": len(r.content)}
    except Exception as e:
        return {"error": str(e)}


def scrape_html(url: str) -> dict:
    """Scrape HTML."""
    try:
        import httpx
        from bs4 import BeautifulSoup
        r = httpx.get(url, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        links = [a.get("href") for a in soup.find_all("a")]
        return {"title": soup.title.string if soup.title else None, "links": links[:20]}
    except Exception as e:
        return {"error": str(e)}


def scrape_json(url: str) -> dict:
    """Scrape JSON."""
    import httpx
    try:
        r = httpx.get(url, timeout=30)
        return {"data": r.json()}
    except Exception as e:
        return {"error": str(e)}


def get_url_info(url: str) -> dict:
    """Get URL info."""
    import httpx
    try:
        r = httpx.head(url, timeout=10, follow_redirects=True)
        return {"url": url, "status": r.status_code, "content_type": r.headers.get("content-type")}
    except Exception as e:
        return {"error": str(e)}


def zip_archive(paths: list, output: str) -> dict:
    """Create ZIP archive."""
    import zipfile
    try:
        with zipfile.ZipFile(output, "w") as zf:
            for p in paths:
                zf.write(p, Path(p).name)
        return {"saved": output, "files": len(paths)}
    except Exception as e:
        return {"error": str(e)}


def zip_extract(path: str, output_dir: str) -> dict:
    """Extract ZIP."""
    import zipfile
    try:
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(output_dir)
        return {"extracted": output_dir}
    except Exception as e:
        return {"error": str(e)}


def qr_code(text: str, path: str = None) -> dict:
    """Generate QR code."""
    if not try_import_image():
        return {"error": "qrcode/PIL not installed"}
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


def read_qr_code(path: str) -> dict:
    """Read QR code."""
    if not try_import_barcode():
        return {"error": "pyzbar not installed"}
    try:
        from PIL import Image
        from pyzbar import decode
        result = decode(Image.open(path))
        return {"data": [r.data.decode() for r in result]}
    except Exception as e:
        return {"error": str(e)}


def password_strength(password: str) -> dict:
    """Calculate password strength."""
    score = 0
    feedback = []
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Use at least 8 characters")
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Add uppercase and lowercase")
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Add numbers")
    if re.search(r"[!@#$%^&*]", password):
        score += 1
    else:
        feedback.append("Add special characters")
    strength = ["very_weak", "weak", "fair", "good", "strong", "very_strong"][score]
    return {"score": score, "strength": strength, "feedback": feedback}


def generate_password(length: int = 16) -> dict:
    """Generate secure password."""
    import secrets
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(chars) for _ in range(length))
    return {"password": password, "length": length}


def cron_expression(cron: str) -> dict:
    """Parse cron expression."""
    parts = cron.split()
    if len(parts) != 5:
        return {"error": "Invalid cron (need 5 parts)"}
    meanings = ["minute", "hour", "day", "month", "weekday"]
    return {"expression": cron, "parts": dict(zip(meanings, parts))}


def calculate_date(base: str, add_days: int = 0) -> dict:
    """Calculate date with offset."""
    try:
        date = datetime.fromisoformat(base)
        result = date + timedelta(days=add_days)
        return {"result": result.isoformat()}
    except ValueError:
        return {"error": "Invalid date format"}


def get_timezone_info(timezone: str = None) -> dict:
    """Get timezone info."""
    try:
        import pytz
        if timezone:
            tz = pytz.timezone(timezone)
            return {"timezone": timezone, "now": datetime.now(tz).isoformat()}
        return {"available": "Use pytz.all_timezones"}
    except ValueError:
        return {"error": "pytz not installed"}