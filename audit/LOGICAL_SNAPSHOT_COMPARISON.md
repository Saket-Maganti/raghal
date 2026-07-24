# Logical Snapshot Comparison

The cleanup folder contains three nested project snapshots. This comparison strips those wrapper prefixes before comparing them to the submitted Git worktree.

- Same logical paths with identical hashes: **492**
- Same logical paths with conflicting hashes: **9**
- Scientifically relevant logical conflicts: **3**

## Scientifically relevant conflicts

- `requirements-full.txt` — 3 snapshots, 2 hashes
- `results/revision/fix_03/disagreement_alignment_n100.csv` — 4 snapshots, 2 hashes
- `scripts/analyze_human_disagreement_labels.py` — 4 snapshots, 2 hashes

No version is selected as authoritative. Use nested Git provenance, generation commands, source traces, and output hashes before adopting any remnant version.
