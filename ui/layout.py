# ui/layout.py
import textwrap


def wrap_lines(text: str, width: int = 52) -> list[str]:
    t = " ".join(text.split())
    return textwrap.wrap(t, width=width) or [""]


def label_height_em(num_lines: int, line_height_em: float = 1.3, pad_em: float = 0.2) -> float:
    # height in em to fit num_lines + a bit of padding
    return num_lines * line_height_em + pad_em
