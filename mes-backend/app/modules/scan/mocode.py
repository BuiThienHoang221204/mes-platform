"""Đọc mã QR thô thành mã MO. Không đụng DB.

    ScanRead                               mã đọc được + phần bị cắt bỏ
    normalize(raw)                         bỏ khoảng trắng, viết hoa
    read_mo_code(raw)                      XM068820 → M068820

Đầu đọc hay chèn tiền tố lạ tuỳ cấu hình, nên server tự cắt phần trước chữ M thay
vì bắt người ở trạm chỉnh máy quét.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

MO_CORE = re.compile(r"M\d{6}(?!\d)")
MO_LOOSE = re.compile(r"M[A-Z0-9]{6}(?![A-Z0-9])")
MO_STRICT = re.compile(r"^M\d{6}$")

_JUNK = {"​", "‌", "‍", "﻿"}


@dataclass(frozen=True)
class ScanRead:
    """Mã đọc được, hoặc `error` là câu tiếng Việt nói vì sao không đọc được."""
    code: str | None
    error: str | None


def normalize(raw: str) -> str:
    """Chuẩn hoá chuỗi thô: bỏ ký tự rác và khoảng trắng, viết hoa."""
    s = unicodedata.normalize("NFKC", str(raw))
    s = "".join(c for c in s if c not in _JUNK and (c.isprintable() or c.isspace()))
    return re.sub(r"\s+", "", s).upper()


def read_mo_code(raw: str) -> ScanRead:
    """Rút mã MO khỏi chuỗi quét. Sửa cả lỗi gõ nhầm O↔0, I/L↔1 trong 6 số sau chữ M."""
    text = normalize(raw)
    if not text:
        return ScanRead(None, "Chuỗi quét rỗng")

    found = list(dict.fromkeys(MO_CORE.findall(text)))

    if not found:
        # Gõ nhầm O thay 0, I hoặc L thay 1 — chỉ sửa trong 6 ký tự sau chữ M
        for chunk in MO_LOOSE.findall(text):
            fixed = "M" + chunk[1:].replace("O", "0").replace("I", "1").replace("L", "1")
            if MO_STRICT.match(fixed):
                found.append(fixed)
        found = list(dict.fromkeys(found))

    if len(found) == 1:
        return ScanRead(found[0], None)
    if len(found) > 1:
        return ScanRead(None, "Quét ra nhiều mã: " + " · ".join(found) + " — quét lại")
    return ScanRead(None, f'Không đọc được mã MO trong "{text[:28]}"')
