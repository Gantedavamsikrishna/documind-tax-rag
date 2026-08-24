"""Split the cleaned Income-tax Act into section-level JSON chunks."""

from __future__ import annotations

import json
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "cleaned" / "income_tax_act_clean.txt"
OUTPUT_PATH = PROJECT_ROOT / "data" / "chunks" / "sections.json"

# Real statutory headings use a number with an optional uppercase suffix,
# for example 10, 10AA, 80C, or 115BBDA.
SECTION_PATTERN = re.compile(r"^(?P<section>\d+[A-Z]*)\.")
CHAPTER_PATTERN = re.compile(r"^CHAPTER\s+[IVXLCDM]+(?:-[A-Z]+)?\s*$")
BRACKET_AFTER_NUMBER = re.compile(r"^\d+[A-Z]*\.\s*\[")
FOOTNOTE_SIGNAL = re.compile(
    r"(w\.e\.f\.?|w\.r\.e\.f\.?|Act No\.|\bIns\.|\bSubs?\.|\bOmtt\.?|"
    r"\bOmitted\b|\bRenumbered\b|\bInserted\b|\bSubstituted\b|\bDeleted\b)",
    re.IGNORECASE,
)
DANGLING_REFERENCE = re.compile(
    r"\b(section|sections|clause|sub-section)\s*$", re.IGNORECASE
)


def leading_number(section: str) -> int:
    """Return the numeric part of a statutory section identifier."""
    match = re.match(r"^\d+", section)
    return int(match.group()) if match else -1


def looks_like_footnote(line: str) -> bool:
    """Identify amendment notes that resemble section headings."""
    return not BRACKET_AFTER_NUMBER.match(line) and bool(FOOTNOTE_SIGNAL.search(line))


def build_sections(text: str) -> list[dict[str, str]]:
    """Create section chunks while excluding notes and cross-reference numbers."""
    chunks: list[dict[str, str]] = []
    chapter = ""
    current_section: str | None = None
    current_section_num = -1
    current_lines: list[str] = []
    previous_nonempty_line = ""

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

        match = SECTION_PATTERN.match(stripped_line)
        is_section = False
        if (
            match
            and not looks_like_footnote(stripped_line)
            and not DANGLING_REFERENCE.search(previous_nonempty_line)
        ):
            candidate = match.group("section")
            candidate_number = leading_number(candidate)
            is_plausible = 0 < candidate_number <= 300
            moves_forward = (
                current_section is None or candidate_number >= current_section_num
            )
            is_section = is_plausible and moves_forward

        if is_section:
            save_current_chunk()
            current_section = match.group("section")
            current_section_num = leading_number(current_section)
            current_lines = [line]
        elif current_section is not None:
            current_lines.append(line)

        if stripped_line:
            previous_nonempty_line = stripped_line

    save_current_chunk()
    return chunks


def main() -> None:
    chunks = build_sections(INPUT_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Sections chunked: {len(chunks)}")
    print(f"Saved chunks to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
