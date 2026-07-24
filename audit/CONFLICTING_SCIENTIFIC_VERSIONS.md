# Conflicting Scientific Versions

No winner was selected for any conflict.

## Direct same-relative-path conflicts

The moved paper tree and submitted artifact contain different versions of:

- `Controlled_RAG___Saket/sections/controlledrag_main.tex`
- `Controlled_RAG___Saket/supplement.tex`
- `Controlled_RAG___Saket/ref.bib`
- `Controlled_RAG___Saket/neurips_2026.pdf`

See `RELATIVE_PATH_CONFLICTS.csv` for every version hash and source folder.

## Logical snapshot conflicts

After stripping the cleanup folder's snapshot wrapper prefixes, 492 logical paths are byte-identical and 9 conflict. The load-bearing scientific conflicts are:

- `scripts/analyze_human_disagreement_labels.py`: the submitted worktree differs from all three cleanup snapshots.
- `results/revision/fix_03/disagreement_alignment_n100.csv`: the submitted output differs from all three cleanup snapshots.
- `requirements-full.txt`: the submitted dependency list differs from the two reviewer snapshots.

The claim/source documents (`CLAIMS_AUDIT.md`, `SOURCE_TRACE.md`, `artifact_manifest.md`, `README.md`, and `README_REPRODUCE.md`) and reviewer ZIP also have version differences. See `LOGICAL_SNAPSHOT_CONFLICTS.csv` and `LOGICAL_SNAPSHOT_COMPARISON.md`.

The paired script/output change is scientifically load-bearing, not formatting-only. The cleanup snapshots compute AUPRC manually after sorting; the submitted worktree uses `sklearn.metrics.average_precision_score`. The reported AUPRCs change:

- DeBERTa: 0.761753 → 0.764813
- second NLI: 0.928433 → 0.928793
- RAGAS-style: 0.886240 → 0.859367

The submitted `CLAIMS_AUDIT.md` cites the latter values. The documented lightweight workflow reproduced them, but the paper/rebuttal must state the metric definition and implementation clearly.

The submitted `requirements-full.txt` also removes `gradio` and `huggingface_hub`, consistent with the reviewer artifact excluding deployment infrastructure.
