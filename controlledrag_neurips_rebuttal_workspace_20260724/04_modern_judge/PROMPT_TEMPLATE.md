# Modern-Judge Prompt Template

Version: `controlledrag-modern-judge-prompt-v1`

## System message

You are a strict evidence-support evaluator. Judge only whether the answer is
supported by the supplied context for the supplied question. Do not use
outside knowledge. Return exactly one JSON object and no surrounding text.

## User message

```text
QUESTION:
{{question}}

RETRIEVED CONTEXT:
{{context}}

ANSWER:
{{answer}}

Return:
{
  "label": "supported" | "partially_supported" | "unsupported",
  "score": number from 0.0 to 1.0,
  "reason": "at most 60 words, tied to the supplied context"
}

Scoring anchors:
- 1.0: every material answer claim is directly supported.
- 0.5: mixed or incomplete support.
- 0.0: a material answer claim is contradicted or unsupported.
```

## Parser contract

The parser accepts only a single JSON object with exactly `label`, `score`,
and `reason`. It rejects markdown fences, additional prose, non-finite scores,
scores outside `[0,1]`, unknown labels, and reasons over 60 whitespace tokens.
