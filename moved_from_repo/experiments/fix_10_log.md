# Fix 10 Log - Scope Deployment Claim Explicitly

**Status:** paper patch written, not wired yet.  
**Weakness addressed:** W10, deployment claim overscoped.

## Required Paper Edits

- Abstract: replace broad wording such as "RAG evaluation has been optimizing
  the wrong quantity" with a scoped claim about short-answer extractive QA.
- Section 8: promote long-form null/non-result into a subsection named
  "Scope of the Paradox."
- Broader impact: say HCPC-v2 is a conservative short-answer deployment
  policy requiring validation before use in long-form settings.

Patch text is in:

`ragpaper/sections/revision/fix_10_scope_deployment.tex`
