"""
Minimal fallback implementation of the stdlib `imghdr` module.
This file exists so environments missing the stdlib `imghdr` can still
import and use the basic `what()` detection used by libraries like Streamlit.

It implements a small set of common image type checks (jpeg, png, gif,
webp, bmp, tiff, ico). Behavior is intentionally small and simple.
"""
from __future__ import annotations

from typing import Optional, Union

def what(file: Union[str, bytes, 'os.PathLike'] | None, h: Optional[bytes] = None) -> Optional[str]:
    """Return a string describing the image type, or None if unknown.

    Args:
        file: filename (path) or None when header bytes provided via `h`.
        h: optional header bytes to inspect.
    """
    # Lazy import to avoid extra imports at module import time
    import os

    if h is None:
        if file is None:
            return None
        try:
            with open(file, 'rb') as f:
                h = f.read(32)
        except Exception:
            return None

    if not isinstance(h, (bytes, bytearray)):
        try:
            h = bytes(h)
        except Exception:
            return None

    if h.startswith(b"\xff\xd8"):
        return 'jpeg'
    if h.startswith(b"\x89PNG\r\n\x1a\n"):
        return 'png'
    if h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    # WEBP: RIFF....WEBP
    if h.startswith(b'RIFF') and len(h) >= 12 and h[8:12] == b'WEBP':
        return 'webp'
    if h.startswith(b'BM'):
        return 'bmp'
    if h.startswith(b'II*\x00') or h.startswith(b'MM\x00*'):
        return 'tiff'
    if h.startswith(b'\x00\x00\x01\x00') or h.startswith(b'\x00\x00\x02\x00'):
        return 'ico'

    return None

# Provide a simple public API similar to stdlib
tests = None

__all__ = ['what']
