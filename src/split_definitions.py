"""Split Section 2 (Definitions) into one chunk per defined clause.

Why: Section 2 crams 50+ unrelated definitions ("capital asset", "assessee",
"previous year", ...) into a single giant chunk. Embedded as one blob, the
vector is an average of everything, so vector search can't zero in on just
one definition. This splits it into one clean chunk per clause so each
definition gets its own, precise embedding.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks" / "sections.json"

# Matches a clause boundary like "(1)", "(1A)", "(14)" at the very start of a line.
CLAUSE_PATTERN = re.compile(r"^\((?P<clause>\d+[A-Z]*)\)\s*")

# Tries to pull out the defined term, e.g. (14) "capital asset" means...
TERM_PATTERN = re.compile(r'^"(?P<term>[^"]+)"\s+means')


def find_canonical_section_2(chunks: list[dict]) -> tuple[dict, list[int]]:
    """Return the longest chunk labeled section '2' (the real body), and the
    indices of ALL chunks labeled '2' (so we can remove every duplicate)."""
    indices = [i for i, c in enumerate(chunks) if c["section"] == "2"]
    if not indices:
        raise ValueError("No chunk with section '2' found in sections.json")
    longest_idx = max(indices, key=lambda i: len(chunks[i]["text"]))
    return chunks[longest_idx], indices


def split_into_clauses(section2_text: str, chapter: str) -> list[dict]:
    """Split Section 2's body text into one chunk per top-level clause."""
    clause_chunks: list[dict] = []
    current_clause: str | None = None
    current_lines: list[str] = []

    def save_current() -> None:
        if current_clause is None:
            return
        body = "\n".join(current_lines).strip()
        term_match = TERM_PATTERN.match(body)
        clause_chunks.append(
            {
                "section": f"2({current_clause})",
                "chapter": chapter,
                "term": term_match.group("term") if term_match else None,
                "text": f"Section 2({current_clause}):\n{body}",
            }
        )

    for line in section2_text.splitlines():
        stripped = line.strip()
        clause_match = CLAUSE_PATTERN.match(stripped)
        if clause_match:
            save_current()
            current_clause = clause_match.group("clause")
            current_lines = [CLAUSE_PATTERN.sub("", stripped, count=1)]
        elif current_clause is not None:
            current_lines.append(line)
        # lines before the first clause match (e.g. "2. In this Act,
        # unless the context otherwise requires,—") are intentionally
        # dropped -- they're a lead-in, not a definition.

    save_current()
    return clause_chunks


def main() -> None:
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))

    canonical, all_section_2_indices = find_canonical_section_2(chunks)
    print(f"Found {len(all_section_2_indices)} chunk(s) labeled '2'.")
    print(f"Canonical Section 2 body length: {len(canonical['text'])} chars")

    clause_chunks = split_into_clauses(canonical["text"], canonical["chapter"])
    print(f"Split into {len(clause_chunks)} individual definition clauses.")

    # Remove every old "2" chunk (canonical + duplicate fragments), then
    # insert the new clause-level chunks in their place.
    insert_at = min(all_section_2_indices)
    kept = [c for i, c in enumerate(chunks) if i not in all_section_2_indices]
    new_chunks = kept[:insert_at] + clause_chunks + kept[insert_at:]

    CHUNKS_PATH.write_text(
        json.dumps(new_chunks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Total chunks now: {len(new_chunks)}")
    print(f"Saved back to: {CHUNKS_PATH}")

    # Quick sanity check
    sample_terms = [c["term"] for c in clause_chunks if c["term"]][:10]
    print(f"Sample extracted terms: {sample_terms}")


if __name__ == "__main__":
    main()