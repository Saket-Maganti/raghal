
# Prompt symmetry audit

Status: `PASS`

Normalization replaces the complete retrieved-context block in the
context-conditioned template with nothing, then normalizes line endings and
blank lines. The normalized result is byte-identical to the answer-only
template.

```diff
 <QUESTION>
 {{QUESTION}}
 </QUESTION>
+<RETRIEVED_CONTEXT>
+{{RETRIEVED_CONTEXT}}
+</RETRIEVED_CONTEXT>
 <ANSWER>
 {{ANSWER}}
 </ANSWER>
```

No other semantic or lexical difference exists. Role, faithfulness
definition, threshold, question/answer order, output schema, and prohibition
on explanations are identical.
