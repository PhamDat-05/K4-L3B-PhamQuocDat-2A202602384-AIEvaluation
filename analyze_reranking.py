"""Measure Exercise 3.5 on saved retrieval traces, preserving the chunk set."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from evaluate_answers import load_evaluation_inputs
from template import RAGASEvaluator, rerank_by_overlap


DEFAULT_IDS = ("M01", "M05", "H01", "H02", "H04")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", type=Path, default=Path("golden_dataset.json"))
    parser.add_argument("--actual", type=Path, default=Path("artifacts/actual_answers.json"))
    parser.add_argument("--ids", nargs="+", default=list(DEFAULT_IDS))
    args = parser.parse_args()

    pairs, _ = load_evaluation_inputs(args.golden, args.actual)
    by_id = {pair.metadata["id"]: pair for pair in pairs}
    evaluator = RAGASEvaluator()
    rows: list[tuple[str, float, float, float, float]] = []
    for case_id in args.ids:
        pair = by_id[case_id]
        before = pair.retrieved_contexts
        after = rerank_by_overlap(before, pair.question)
        if Counter(after) != Counter(before):
            raise AssertionError(f"Reranker changed the chunk set for {case_id}")
        rows.append((
            case_id,
            evaluator.evaluate_context_recall(before, pair.expected_answer),
            evaluator.evaluate_context_recall(after, pair.expected_answer),
            evaluator.evaluate_context_precision(before, pair.expected_answer),
            evaluator.evaluate_context_precision(after, pair.expected_answer),
        ))

    print("| ID | Recall before | Recall after | Precision before | Precision after | Delta Precision |")
    print("|---|---:|---:|---:|---:|---:|")
    for case_id, recall_before, recall_after, precision_before, precision_after in rows:
        print(
            f"| {case_id} | {recall_before:.3f} | {recall_after:.3f} | "
            f"{precision_before:.3f} | {precision_after:.3f} | "
            f"{precision_after - precision_before:+.3f} |"
        )
    if rows:
        averages = [sum(row[column] for row in rows) / len(rows) for column in range(1, 5)]
        print(
            f"| **Avg** | {averages[0]:.3f} | {averages[1]:.3f} | "
            f"{averages[2]:.3f} | {averages[3]:.3f} | "
            f"{averages[3] - averages[2]:+.3f} |"
        )


if __name__ == "__main__":
    main()
