"""Evaluate DocuMind's retrieval and citation accuracy against a known test set."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from query_engine import answer_query


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_SET_PATH = PROJECT_ROOT / "data" / "eval" / "test_questions.json"
RESULTS_PATH = PROJECT_ROOT / "data" / "eval" / "results.json"


def normalize(section: str) -> str:
    """Loose-match section ids, e.g. '2(14)' should match '2(14)' or '2( 14 )'."""
    return re.sub(r"\s+", "", section).upper()


def evaluate_one(item: dict) -> dict:
    question = item["question"]
    expected = [normalize(s) for s in item.get("expected_sections", [])]
    expect_insufficient = item.get("expect_insufficient_context", False)

    try:
        answer, retrieved_sections = answer_query(question)
    except Exception as error:  # noqa: BLE001 - eval harness should never crash mid-run
        return {
            "question": question,
            "error": str(error),
            "retrieval_hit": False,
            "citation_hit": False,
            "hallucination_check_passed": False,
        }

    retrieved_normalized = [normalize(s) for s in retrieved_sections]

    # Retrieval accuracy: did the correct section even get pulled from Chroma?
    retrieval_hit = (
        any(e in retrieved_normalized for e in expected) if expected else None
    )

    # Citation accuracy: did the LLM's answer text actually cite the right section?
    answer_upper = answer.upper()
    citation_hit = (
        any(e in answer_upper.replace(" ", "") for e in expected)
        if expected
        else None
    )

       # Normalize curly quotes to straight quotes so phrase matching isn't
    # broken by the model's typography choices.
    normalized_answer = (
        answer.lower()
        .replace("\u2019", "'")  # curly apostrophe -> straight
        .replace("\u2018", "'")
    )
    refusal_phrases = [
        "insufficient", "does not contain", "does not provide", "does not mention",
        "cannot provide", "cannot answer", "not contain", "no information",
        "i'm sorry", "i am sorry", "unable to answer", "not available in",
    ]
    declined = any(phrase in normalized_answer for phrase in refusal_phrases)
    hallucination_check_passed = declined if expect_insufficient else None

    return {
        "question": question,
        "expected_sections": expected,
        "retrieved_sections": retrieved_normalized,
        "retrieval_hit": retrieval_hit,
        "citation_hit": citation_hit,
        "hallucination_check_passed": hallucination_check_passed,
        "answer_preview": answer[:200],
    }


def main() -> None:
    test_set = json.loads(TEST_SET_PATH.read_text(encoding="utf-8"))
    results = []

    print(f"Running evaluation on {len(test_set)} questions...\n")
    for i, item in enumerate(test_set, start=1):
        print(f"[{i}/{len(test_set)}] {item['question'][:60]}...")
        result = evaluate_one(item)
        results.append(result)
        time.sleep(1)  # be polite to the free Groq rate limit

    # Aggregate metrics
    retrieval_results = [r["retrieval_hit"] for r in results if r["retrieval_hit"] is not None]
    citation_results = [r["citation_hit"] for r in results if r["citation_hit"] is not None]
    hallucination_results = [
        r["hallucination_check_passed"] for r in results
        if r["hallucination_check_passed"] is not None
    ]

    retrieval_accuracy = sum(retrieval_results) / len(retrieval_results) if retrieval_results else 0
    citation_accuracy = sum(citation_results) / len(citation_results) if citation_results else 0
    hallucination_resistance = (
        sum(hallucination_results) / len(hallucination_results) if hallucination_results else 0
    )

    summary = {
        "total_questions": len(test_set),
        "retrieval_accuracy": round(retrieval_accuracy * 100, 1),
        "citation_accuracy": round(citation_accuracy * 100, 1),
        "hallucination_resistance": round(hallucination_resistance * 100, 1),
        "results": results,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 50)
    print(f"Retrieval accuracy:        {summary['retrieval_accuracy']}%")
    print(f"Citation accuracy:         {summary['citation_accuracy']}%")
    print(f"Hallucination resistance:  {summary['hallucination_resistance']}%")
    print("=" * 50)
    print(f"\nFull results saved to: {RESULTS_PATH}")

    # Print any failures for quick debugging
    failures = [r for r in results if r.get("retrieval_hit") is False or r.get("citation_hit") is False]
    if failures:
        print(f"\n{len(failures)} question(s) with issues:")
        for f in failures:
            print(f"  - {f['question'][:60]}")
            print(f"    expected: {f.get('expected_sections')}, got: {f.get('retrieved_sections')}")


if __name__ == "__main__":
    main()