
# Notebook validation report

Status: `PASS_PREPARATION_PATH`

- JSON notebook parses with nbformat.
- All code cells compile.
- Restart-and-run preparation path completes with authorization false.
- Input paths resolve relative to the private bundle.
- No local absolute path or secret is embedded.
- Two-rank torchrun command is frozen and syntactically validated.
- Synthetic parser/schema/sharding/statistics/packaging tests pass.
- Clean-kernel receipt: 24 test methods pass.
- `AUTHORIZE_REAL_INFERENCE=False` prevents tokenizer/model loading and real
  inference.
- False path ends with
  `PREPARATION_VALIDATED_REAL_INFERENCE_NOT_AUTHORIZED`.

The notebook was not run against real rows or model weights locally.
