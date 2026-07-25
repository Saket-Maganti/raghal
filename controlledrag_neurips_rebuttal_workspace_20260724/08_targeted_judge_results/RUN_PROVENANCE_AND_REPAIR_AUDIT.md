# Run provenance and repair audit

The first run completed all 1,510 requests but used right padding for batched decoder-only generation. Strict validity was 826/1,510, with a large interface imbalance consistent with shorter prompts generating from padding positions.

The only authorized execution repair was:

```python
tokenizer.padding_side = "left"
```

The repair lock reports:

```text
repair_kind = decoder_only_left_padding_only
scientific_changes = []
```

Unchanged elements:

- frozen rows and pair manifests;
- prompt templates, rubric, and two interfaces;
- model and immutable revision;
- NF4 quantization and decoding;
- batch size and maximum output length;
- strict parser and score threshold;
- metrics, bootstrap plan, and inclusion gates.

The accepted repair run produced 1,507 strictly valid outputs and preserved three threshold-inconsistent objects. No output was recoded, repaired, imputed, or combined with the first run.

The original validator's `ok=false` means the run was not 100% valid. It is not the preregistered inclusion decision. Independent application of the preregistered gate yields `STRONG_INCLUSION_GATE_PASS`.
