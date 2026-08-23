"""Remove PDF-export artifacts from the Income-tax Act source text."""

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "income_tax_act_1961.txt"
OUTPUT_PATH = PROJECT_ROOT / "data" / "cleaned" / "income_tax_act_clean.txt"

NOISE_PATTERNS = (
    re.compile(r"^INCOME-TAX ACT, 1961\s*-\s*\d{4}\s*$", re.IGNORECASE),
    re.compile(r"^\d+\s+of\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(?:AM|PM)\s*$", re.IGNORECASE),
)


def is_export_noise(line: str) -> bool:
    """Return whether a line contains a standalone PDF export artifact."""
    return any(pattern.fullmatch(line) for pattern in NOISE_PATTERNS)


def clean_text(source: str) -> tuple[list[str], int]:
    """Strip form feeds and discard only recognized standalone noise lines."""
    cleaned_lines: list[str] = []
    removed_lines = 0

    for line in source.splitlines():
        line = line.replace("\f", "")
        if is_export_noise(line.strip()):
            removed_lines += 1
            continue
        cleaned_lines.append(line)

    return cleaned_lines, removed_lines


def main() -> None:
    source = INPUT_PATH.read_text(encoding="utf-8")
    original_lines = source.splitlines()
    cleaned_lines, removed_lines = clean_text(source)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(cleaned_lines) + "\n", encoding="utf-8")

    print(f"Original line count: {len(original_lines)}")
    print(f"Cleaned line count: {len(cleaned_lines)}")
    print(f"Lines removed: {removed_lines}")


if __name__ == "__main__":
    main()
