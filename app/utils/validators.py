"""
Server-side input validation (SDS Section 7 - Security Design, NFR-2.3).

All form and file inputs are validated server-side (file type/size for
images, field presence/format for forms) before being processed or stored.
"""
import os


def allowed_image_file(filename: str, allowed_extensions: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def is_within_max_size(file_storage, max_content_length: int) -> bool:
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    return size <= max_content_length


def require_fields(form: dict, fields: list) -> list:
    """Returns a list of missing/blank required field names from a form dict."""
    return [f for f in fields if not (form.get(f) or "").strip()]
