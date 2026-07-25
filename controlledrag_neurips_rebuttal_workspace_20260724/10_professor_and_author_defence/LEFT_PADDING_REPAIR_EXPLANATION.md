# Left-padding repair explanation

Decoder-only models generate the next token after the final token in each prompt. In a variable-length batch, right padding places padding tokens after shorter prompts. Generation can then start from the padding position rather than the prompt's actual end.

That happened in the first run. All 1,510 requests completed, but answer-only prompts, usually shorter than context-conditioned prompts, failed strict parsing much more often. Rows at the maximum length of their batch were almost all valid, which isolates the padding mechanism.

The repair was one line:

```python
tokenizer.padding_side = "left"
```

Left padding aligns every prompt's real final token at the right edge. It does not change the text, model, revision, rows, rubric, interface, threshold, parser, decoding, metrics, or bootstrap plan.

The repair run received all 1,510 outputs and produced 1,507 strictly valid objects. Three threshold inconsistencies remain invalid. No output was edited. The first and repair runs were not combined.
