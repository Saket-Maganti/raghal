
# Kaggle runbook

1. Create a new **private** Kaggle dataset.
2. Upload `CONTROLLEDRAG_TARGETED_JUDGE_INPUT.zip`.
3. Create/open the included notebook.
4. Select accelerator `GPU T4 ×2`.
5. Enable Internet only if needed for pinned dependency/model retrieval.
6. Attach the private input dataset.
7. Verify the model ID and immutable revision displayed by the notebook.
8. Keep `AUTHORIZE_REAL_INFERENCE=False` and run preparation cells once.
9. Confirm all preparation checks pass.
10. Change only `AUTHORIZE_REAL_INFERENCE = True`.
11. Restart and Run All.
12. Do not edit prompts, manifests, model revision, metrics, or thresholds.
13. Download `CONTROLLEDRAG_TARGETED_JUDGE_OUTPUT.zip`.
14. Return that ZIP for Prompt B.
15. Do not interpret or selectively rerun based on preliminary output direction.

Estimated real inference runtime: approximately 45 minutes to 2 hours,
excluding model download and Kaggle queue/startup.
