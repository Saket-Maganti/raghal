# Human Evaluation Instructions: Targeted Disagreement Batch

## Overview
This task involves evaluating the faithfulness of AI-generated answers in a Retrieval-Augmented Generation (RAG) system. You will be presented with a question, a retrieved context (evidence), and a generated answer.

## Core Goal
Your task is to determine if the **generated answer** is fully supported by the **retrieved context**.

## The Core Rule
**Judge the generated answer against the retrieved context ONLY.**
- Do NOT use your own outside knowledge.
- Do NOT judge the answer merely by how well it matches the "gold answer" (if provided).
- If the context contains a factually incorrect statement and the model repeats it, the answer is still considered **faithful** to that context.
- If the context is missing information required to answer the question, but the model provides a correct answer using its own internal knowledge, the answer is **hallucinated** relative to the provided context.

## Labels
You will assign one of the following labels:

- **faithful**: every factual claim in the generated answer is supported by the retrieved context.
- **hallucinated**: at least one factual claim in the generated answer is unsupported or contradicted by the retrieved context.
- **unclear**: the context or answer is too ambiguous, incomplete, or underspecified for a reliable binary decision.

## Confidence
Assign a confidence score for your label:
- **1**: Low confidence (could easily go either way)
- **2**: Medium confidence
- **3**: High confidence (very clear case)

## Notes
Provide brief notes for any case labeled "hallucinated" or "unclear", or for "faithful" cases that were borderline.
