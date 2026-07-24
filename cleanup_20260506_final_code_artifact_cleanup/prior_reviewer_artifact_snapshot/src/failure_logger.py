"""
Failure Logger

Captures per-query results — retrieved context, generated output, NLI scores,
and retrieval quality metrics — into structured JSON for post-hoc analysis
and paper reporting.

Usage
-----
    from src.failure_logger import FailureLogger

    logger = FailureLogger("results/adaptive/run_logs.json", log_all=True)

    logger.log(
        query="What city hosted Super Bowl 50?",
        retrieved_context="...",
        generated_output="San Francisco Bay Area",
        faithfulness_score=0.4784,
        is_hallucination=True,
        sentence_scores=[...],          # from HallucinationDetector
        retrieval_metrics={...},        # from compute_retrieval_quality
        metadata={"chunk_size": 256, "strategy": "fixed", ...},
    )

    logger.save()     # writes JSON to output_path
    logger.to_csv()   # writes flattened CSV alongside the JSON

Set log_all=False to capture only hallucinated cases.
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from typing import Optional


class FailureLogger:
    """
    Accumulates per-query result records and serializes them to JSON (and
    optionally CSV) for analysis.

    Parameters
    ----------
    output_path : destination path for the JSON file
    log_all     : True  → log every query result
                  False → log only cases where is_hallucination is True
    """

    def __init__(self, output_path: str, log_all: bool = True):
        self.output_path = output_path
        self.log_all = log_all
        self.records: list[dict] = []
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # ── Logging ───────────────────────────────────────────────────────────────

    def log(
        self,
        query: str,
        retrieved_context: str,
        generated_output: str,
        faithfulness_score: float,
        is_hallucination: bool,
        sentence_scores: Optional[list[dict]] = None,
        retrieval_metrics: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Record one query result.

        Parameters
        ----------
        query              : the input question
        retrieved_context  : concatenated retrieved chunk text
        generated_output   : the LLM's answer
        faithfulness_score : mean NLI entailment score [0, 1]
        is_hallucination   : True if faithfulness_score < 0.5
        sentence_scores    : per-sentence NLI breakdown from HallucinationDetector
        retrieval_metrics  : dict from compute_retrieval_quality
        metadata           : any extra fields (chunk_size, strategy, model, ...)
        """
        if not self.log_all and not is_hallucination:
            return

        record: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            # Cap context at 2000 chars so the JSON file stays readable
            "retrieved_context": retrieved_context[:2000] if retrieved_context else "",
            "generated_output": generated_output,
            "faithfulness_score": round(float(faithfulness_score), 4),
            "is_hallucination": bool(is_hallucination),
            "sentence_scores": sentence_scores or [],
            "retrieval_metrics": retrieval_metrics or {},
            "metadata": metadata or {},
        }
        self.records.append(record)

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self) -> int:
        """Write records to JSON. Returns number of records written."""
        with open(self.output_path, "w", encoding="utf-8") as fh:
            json.dump(self.records, fh, indent=2, ensure_ascii=False)
        print(f"[FailureLogger] {len(self.records)} records → {self.output_path}")
        return len(self.records)

    def to_csv(self, csv_path: Optional[str] = None) -> str:
        """
        Write a flattened CSV alongside the JSON.

        Nested fields (sentence_scores, retrieval_metrics, metadata) are
        serialized as JSON strings so they survive round-trips through
        spreadsheet tools.

        Returns the path of the written CSV.
        """
        if not self.records:
            print("[FailureLogger] No records to export.")
            return ""

        path = csv_path or self.output_path.replace(".json", ".csv")

        # Collect all unique flat keys from every record
        flat_keys: list[str] = [
            "timestamp", "query", "retrieved_context", "generated_output",
            "faithfulness_score", "is_hallucination",
        ]

        # Expand retrieval_metrics keys as separate columns
        ret_keys: set[str] = set()
        meta_keys: set[str] = set()
        for rec in self.records:
            ret_keys.update(rec.get("retrieval_metrics", {}).keys())
            meta_keys.update(rec.get("metadata", {}).keys())

        all_keys = (
            flat_keys
            + [f"ret_{k}" for k in sorted(ret_keys)]
            + sorted(meta_keys)
            + ["sentence_scores"]
        )

        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=all_keys, extrasaction="ignore")
            writer.writeheader()
            for rec in self.records:
                row: dict = {k: rec.get(k, "") for k in flat_keys}
                for k in ret_keys:
                    row[f"ret_{k}"] = rec.get("retrieval_metrics", {}).get(k, "")
                for k in meta_keys:
                    row[k] = rec.get("metadata", {}).get(k, "")
                row["sentence_scores"] = json.dumps(rec.get("sentence_scores", []))
                writer.writerow(row)

        print(f"[FailureLogger] CSV written → {path}")
        return path

    # ── Summary helpers ───────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Return aggregate statistics over logged records."""
        if not self.records:
            return {}

        n = len(self.records)
        n_halluc = sum(1 for r in self.records if r["is_hallucination"])
        scores = [r["faithfulness_score"] for r in self.records]
        sims = [
            r["retrieval_metrics"].get("mean_similarity", None)
            for r in self.records
            if r["retrieval_metrics"].get("mean_similarity", -1.0) >= 0
        ]

        result: dict = {
            "n_total": n,
            "n_hallucinated": n_halluc,
            "hallucination_rate": round(n_halluc / n, 4),
            "mean_faithfulness": round(sum(scores) / n, 4),
            "min_faithfulness": round(min(scores), 4),
            "max_faithfulness": round(max(scores), 4),
        }
        if sims:
            result["mean_retrieval_similarity"] = round(sum(sims) / len(sims), 4)

        return result

    def __len__(self) -> int:
        return len(self.records)

    def __repr__(self) -> str:
        return (
            f"FailureLogger(records={len(self.records)}, "
            f"log_all={self.log_all}, path={self.output_path!r})"
        )
