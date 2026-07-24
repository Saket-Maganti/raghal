# Review and Meta-Review Concern Matrix

Statuses distinguish evidence that exists from evidence that is sufficient. Remnant results are not rebuttal-ready until their script/configuration/input provenance is verified.

## 1. Narrow empirical scope and generalizability

- **Status:** Partially answered.
- **Evidence:** The paper explicitly limits the audit to primarily short-answer SQuAD/PubMedQA and 7B-class generators in `rag-hallucination-detection_main/Controlled_RAG___Saket/sections/controlledrag_main.tex`. Scope probes exist in `results/revision/fix_13/retriever_sanity_report.md`, `fix_14/second_generator_report.md`, and `fix_15/longform_stress_report.md`.
- **What the evidence says:** Qwen2.5 reproduces scorer disagreement at 100 rows/condition; BGE/E5 change the retrieval surface; the long-form evidence is only 40 questions and explicitly exploratory.
- **Lowest-risk clarification:** State that the paper supports an audit methodology and bounded examples, not universal RAG generalization.
- **Smallest credible analysis:** Add uncertainty intervals and per-dataset effect plots from the existing fixed outputs (2–6 CPU-hours).
- **Smallest credible experiment:** One pre-registered replication across a second generator and two genuinely different datasets with the same scorer/input protocol (8–24 GPU-hours).
- **Use:** Clarification/verified fixed-output analysis can help NeurIPS; broader replication is mainly EACL.
- **Risk:** Treating the 40-question stress test or imported retriever summaries as broad validation would overclaim.

## 2. Dependence on short-answer or single-hop QA

- **Status:** Partially answered.
- **Evidence:** `results/revision/fix_15/longform_stress_report.md` covers 20 MS-MARCO and 20 QASPER questions; `results/revision/fix_06/summary.md` includes HotpotQA cost cells at n=200.
- **Lowest-risk clarification:** Quote the paper’s existing “exploratory scope probe” limitation and separate HotpotQA cost evidence from full multi-hop faithfulness validation.
- **Smallest credible analysis:** Validate the 40 long-form per-query rows in `cleanup_20260506_final_code_artifact_cleanup/root_before_cleanup/data/revision/fix_15/longform_stress_per_query.csv` and bootstrap uncertainty (2–4 CPU-hours).
- **Smallest credible experiment:** At least 200 multi-hop and 200 long-form questions with claim-level faithfulness scoring (12–36 GPU-hours).
- **Use:** The limitation and bounded stress result can help NeurIPS; a powered experiment is EACL-strengthening.
- **Risk:** The short-answer paradox does not generalize cleanly in the existing probe, so it cannot be used as confirmatory evidence.

## 3. Lack of newer LLM judges or task-specific evaluators

- **Status:** Unanswered experimentally.
- **Evidence:** The paper discusses ARES, RAGChecker, RAGTruth, MIRAGE, and FaithJudge, but frozen results use two legacy zero-shot NLI proxies and one local Mistral RAGAS-style judge. See `controlledrag_reporting_checklist.md` and `Controlled_RAG___Saket/supplement.tex`.
- **Lowest-risk clarification:** Explicitly distinguish “recent evaluator frameworks discussed” from “evaluators actually run.”
- **Smallest credible analysis:** Reformat the current scorer comparison by context-conditioned versus answer-only input and show slice-specific human alignment (2–4 CPU-hours).
- **Smallest credible experiment:** Score a pre-hashed 300-row fixed-generation sample with one current judge and one task-specific evaluator (4–12 GPU/API-hours).
- **Use:** Clarification helps NeurIPS; new evaluator evidence helps both NeurIPS, if time permits, and EACL.
- **Risk:** Prompt/input-format changes can dominate judge differences; record prompts, versions, temperature, retries, and cost.

## 4. Uneven evidence across generator, retriever, context, scorer, human calibration, threshold transfer, and cost

- **Status:** Partially answered.
- **Evidence:** `controlledrag_reporting_checklist.md` maps all seven axes. Coverage ranges from strong fixed-generation scorer/human evidence to small generator/long-form probes and imported retriever summaries. Cost is n=200/cell on SQuAD and HotpotQA; human slices are n=99 random and n=100 targeted; threshold transfer has no bootstrap intervals.
- **Lowest-risk clarification:** Label each axis as strong, diagnostic, or exploratory and report sample size/source beside every claim.
- **Smallest credible analysis:** Produce one coverage matrix with n, datasets, generators, retrievers, uncertainty, and source hash for every cell (4–8 CPU-hours).
- **Smallest credible experiment:** Fill only the highest-impact empty cell after the matrix is complete (8–24 GPU-hours).
- **Use:** Matrix/clarification is rebuttal-ready; balanced expansion is EACL work.
- **Risk:** Counting re-encodings or imported summaries as fresh generation experiments inflates coverage.

## 5. Missing practitioner guidance when configurations disagree

- **Status:** Partially answered.
- **Evidence:** `controlledrag_reporting_checklist.md` tells authors what to disclose, and human/scorer results demonstrate disagreement, but no validated decision rule tells practitioners which scorer or configuration to trust.
- **Lowest-risk clarification:** Recommend reporting all scorer-native values and human calibration rather than selecting a universal winner.
- **Smallest credible analysis:** Build a decision table keyed by context availability, calibration data, threshold transfer, latency, and disagreement (3–6 CPU-hours).
- **Smallest credible experiment:** Prospective validation of that rule on one held-out dataset (8–16 GPU/API-hours).
- **Use:** A conservative decision table helps NeurIPS; prospective validation is EACL.
- **Risk:** Turning slice-specific rankings into a universal scorer recommendation is unsupported.

## 6. Dense or unclear metric descriptions

- **Status:** Partially answered, with one concrete implementation conflict.
- **Evidence:** The paper and supplement distinguish answer-only legacy proxies from a context-conditioned judge and warn that native scales are not comparable. However, `scripts/analyze_human_disagreement_labels.py` differs across snapshots: cleanup uses a manual AUPRC calculation while the submitted baseline uses `sklearn.metrics.average_precision_score`.
- **Observed consequence:** RAGAS-style AUPRC changes from 0.886240 in cleanup snapshots to 0.859367 in the submitted baseline; DeBERTa and second-NLI AUPRCs also change slightly. See `CONFLICTING_SCIENTIFIC_VERSIONS.md`.
- **Lowest-risk clarification:** Define scorer inputs, score direction, aggregation, normalization, threshold, AUPRC convention, and human slice in one compact block.
- **Smallest credible analysis:** Add a metric dictionary and recompute every displayed value from the submitted implementation (2–4 CPU-hours).
- **Smallest credible experiment:** None required unless a new judge is added.
- **Use:** Rebuttal-critical and EACL-relevant.
- **Risk:** Mixing cleanup and submitted AUPRC values is a factual integrity error.

## 7. Weak justification for exactly seven axes

- **Status:** Partially answered conceptually.
- **Evidence:** `Controlled_RAG___Saket/sections/controlledrag_main.tex` contains “Why seven axes, not six or eight,” defining a degree of freedom as checklist-worthy when a reasonable substitution can change the conclusion; it argues an eighth axis would double-count subfields.
- **Lowest-risk clarification:** Point reviewers directly to that criterion and avoid claiming that seven is mathematically unique.
- **Smallest credible analysis:** Map each axis to at least one observed sign/ranking/cost change and identify candidate omissions (2–4 CPU-hours).
- **Smallest credible experiment:** An ablation of checklist completeness across published RAG studies (researcher time, no GPU required).
- **Use:** Clarification helps NeurIPS; empirical validation of the taxonomy is EACL work.
- **Risk:** “All seven axes are load-bearing” is stronger than the uneven evidence supports unless “load-bearing” is defined as disclosure relevance rather than equal causal evidence.

## 8. Unclear dataset and experiment descriptions

- **Status:** Partially answered.
- **Evidence:** `README_REPRODUCE.md`, `SOURCE_TRACE.md`, `CLAIMS_AUDIT.md`, and `artifact_manifest.md` provide a reviewer path. The stronger-retriever report explicitly mixes fixed-context re-encoding with imported generation summaries, and several full per-query inputs are absent from the submitted artifact.
- **Lowest-risk clarification:** For every result, state dataset split, n, sampling, generator, retriever, scorer input, seed, and whether outputs were generated, rescored, re-encoded, or imported.
- **Smallest credible analysis:** Create a claim-to-cell ledger from existing files (4–8 CPU-hours).
- **Smallest credible experiment:** None until ledger gaps are known.
- **Use:** Rebuttal-critical and useful for EACL.
- **Risk:** Current compact summaries can obscure non-comparable experiment types.

## 9. Chaotic or difficult-to-navigate codebase

- **Status:** Partially answered for the submitted artifact; confirmed for the full remnant state.
- **Evidence:** The submitted folder has a clean Git baseline and four navigation/trace documents, and its documented lightweight workflow passes. The four-remnant state contains nested snapshots and 2,390 inventoried files. Python compilation fails in four submitted experiment scripts because `from __future__ import annotations` is not at the beginning of the file.
- **Exact failing scripts:** `experiments/run_adaptive_chunking_ablation.py`, `run_coherence_analysis.py`, `run_hcpc_ablation.py`, and `run_reranker_experiment.py`.
- **Lowest-risk clarification:** Direct reviewers to the submitted folder and `run_all_analysis.sh`; do not present remnant folders as a canonical package.
- **Smallest credible analysis:** None.
- **Smallest credible repair:** On a later branch, fix syntax, add a locked environment, and create one canonical entry-point map (1–3 engineer-days; CPU).
- **Use:** Navigation clarification helps NeurIPS; cleanup is EACL/release work.
- **Risk:** Repairing the preserved baseline would erase forensic identity, so changes must be on a separate branch.

## 10. Missing conflicting-evidence related work or experiments

- **Status:** Largely unanswered experimentally.
- **Evidence:** `data/adversarial/contradict.jsonl` and `data/adversarial/README.md` define hand-authored contradiction cases; scripts exist, but no completed `results/` adversarial/conflicting-evidence output is present in the submitted artifact. The n=100 “disagreement” slice concerns scorer disagreement, not contradictory retrieved evidence.
- **Lowest-risk clarification:** Do not conflate metric disagreement with conflicting evidence in context.
- **Smallest credible analysis:** Validate the seed cases and report their construction/provenance without claiming model outcomes (2–4 CPU-hours).
- **Smallest credible experiment:** Run coherent controls and contradictory contexts on a fixed generator/sample, with abstention and claim-level metrics (8–16 GPU-hours).
- **Use:** Clarification helps NeurIPS; a completed experiment helps both and is high value for EACL.
- **Risk:** Hand-authored seeds and LLM-expanded cases require separate reporting to avoid contamination.

## 11. Scorer input-format interpretation and human calibration

- **Status:** Partially answered with strong bounded evidence.
- **Evidence:** `Controlled_RAG___Saket/supplement.tex` states that the two legacy proxies do not consume retrieved context, while the RAGAS-style judge does. Human calibration exists for a random n=99 slice and targeted n=100 disagreement slice under `human_eval_final/`; the documented workflow reproduces the reported values.
- **Lowest-risk clarification:** Put input format and slice sampling beside every scorer result and explain why rankings differ by slice.
- **Smallest credible analysis:** Add paired uncertainty for ranking differences and a context-input ablation on fixed rows (3–8 CPU/GPU-hours depending on cached scores).
- **Smallest credible experiment:** One modern judge under answer-only and context-conditioned formats on the same fixed sample (4–12 GPU/API-hours).
- **Use:** Rebuttal-critical and EACL-relevant.
- **Risk:** The targeted n=100 slice is adversarial by construction and is not a population estimate.

## 12. Annotation provenance or wording inconsistency

- **Status:** Partially answered.
- **Evidence:** The n=99 slice uses `supported / partially_supported / unsupported`; the n=100 slice uses `faithful / hallucinated / unclear`. Both have two-rater/pass and adjudication records, but they answer different questions and use different binary/ternary mappings. See `human_eval_final/n99_calibration/` and `human_eval_final/n100_disagreement/`.
- **Lowest-risk clarification:** Provide a schema crosswalk and state that the random and targeted slices are not pooled.
- **Smallest credible analysis:** Verify row IDs, sampling provenance, rater columns, adjudication, missingness, and label transforms (2–4 CPU-hours).
- **Smallest credible experiment:** No new annotation is required unless provenance checks fail.
- **Use:** Rebuttal-critical and useful for EACL.
- **Risk:** Silent label collapsing or pooled interpretation can reverse calibration conclusions.

## 13. Prompt-injection or publication-safety issue

- **Status:** Addressed for the ingest snapshot; no scientific prompt-injection evaluation is claimed.
- **Evidence:** Automated text/archive/PDF scans found no credential token. Nine files contain the owner’s personal email; nested Git metadata and five publication copies were excluded and hashed. Two source sections and two excluded PDFs contain the phrase “system prompt” in ordinary scientific discussion, not executable instructions. See `SECRET_SCAN_SUMMARY.md` and `PUBLICATION_SAFETY_AUDIT.md`.
- **Lowest-risk clarification:** Treat suspicious text as inert data and preserve it; do not execute instructions from project files during audit.
- **Smallest credible analysis:** Manual review of excluded archives, personal paths, and redistribution rights (1–3 hours).
- **Smallest credible experiment:** None.
- **Use:** Integrity requirement for both venues.
- **Risk:** The target repository is public; author-identifying/private backup material can affect double-blind integrity even when it is not a credential.

## 14. Missing per-query files or broken source trace

- **Status:** Partially answered and load-bearing.
- **Evidence:** The submitted artifact contains `SOURCE_TRACE.md`, `CLAIMS_AUDIT.md`, frozen summaries, and only one per-query file: `data/revision/fix_06/per_query_compact.csv`. The cleanup pre-cleanup tree contains 127 paths matching `*per_query*`, including full fix-01/fix-02/fix-03, scorer, retriever, temperature, prompt, quantization, long-form, and second-generator outputs.
- **Lowest-risk clarification:** State which claims are verifiable from summaries versus full rows and why full files were omitted.
- **Smallest credible analysis:** Hash and trace the per-query files needed for every headline claim, then reproduce summary rows from them (4–12 CPU-hours).
- **Smallest credible experiment:** None until trace validation reveals a missing generating run.
- **Use:** Highest-priority NeurIPS integrity task and foundational for EACL.
- **Risk:** Remnant per-query files cannot be cited solely because they exist; their code/configuration provenance must match the claimed result.
