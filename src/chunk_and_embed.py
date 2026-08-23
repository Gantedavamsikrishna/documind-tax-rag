"""Split the cleaned Income-tax Act into section-level JSON chunks."""

from __future__ import annotations

import json
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "cleaned" / "income_tax_act_clean.txt"
OUTPUT_PATH = PROJECT_ROOT / "data" / "chunks" / "sections.json"

# Covers statutory identifiers such as 2, 80C, 10AA, and 10(23C).
SECTION_PATTERN = re.compile(r"^(?P<section>\d+[A-Za-z]*(?:\([0-9A-Za-z]+\))*)\.")
CHAPTER_PATTERN = re.compile(r"^CHAPTER\s+[IVXLCDM]+(?:-[A-Z]+)?\s*$")


def build_sections(text: str) -> list[dict[str, str]]:
    """Create one chunk per statute section, retaining its nearest chapter."""
    chunks: list[dict[str, str]] = []
    chapter = ""
    current_section: str | None = None
    current_lines: list[str] = []

    def save_current_chunk() -> None:
        if current_section is not None:
            chunks.append(
                {
                    "section": current_section,
                    "chapter": chapter,
                    "text": "\n".join(current_lines).strip(),
                }
            )

    for line in text.splitlines():
        stripped_line = line.strip()
        if CHAPTER_PATTERN.fullmatch(stripped_line):
            chapter = stripped_line

        section_match = SECTION_PATTERN.match(stripped_line)
        if section_match:
            save_current_chunk()
            current_section = section_match.group("section")
            current_lines = [line]
        elif current_section is not None:
            current_lines.append(line)

    save_current_chunk()
    return chunks


def main() -> None:
    text = INPUT_PATH.read_text(encoding="utf-8")
    chunks = build_sections(text)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Sections chunked: {len(chunks)}")
    print(f"Saved chunks to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
