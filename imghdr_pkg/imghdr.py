"""
Fallback imghdr module packaged for pip install.
This file mirrors the top-level `imghdr.py` fallback.
"""
from __future__ import annotations

from typing import Optional, Union

def what(file: Union[str, bytes, 'os.PathLike'] | None, h: Optional[bytes] = None) -> Optional[str]:
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
    if h.startswith(b'RIFF') and len(h) >= 12 and h[8:12] == b'WEBP':
        return 'webp'
    if h.startswith(b'BM'):
        return 'bmp'
    if h.startswith(b'II*\x00') or h.startswith(b'MM\x00*'):
        return 'tiff'
    if h.startswith(b'\x00\x00\x01\x00') or h.startswith(b'\x00\x00\x02\x00'):
        return 'ico'

    return None

tests = None

__all__ = ['what']
