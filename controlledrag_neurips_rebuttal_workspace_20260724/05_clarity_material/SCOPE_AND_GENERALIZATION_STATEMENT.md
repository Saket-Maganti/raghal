# Scope and Generalization Statement

## Methodological contribution

ControlledRAG is a disclosure and audit protocol for making RAG
faithfulness claims inspectable across seven decision-relevant categories.
Its methodological contribution is the procedure: identify the claim-critical
choices, state what was held fixed and varied, report measurement and human
calibration details, and separate robust findings from conditional or
unresolved ones. This protocol is applicable beyond any one numerical cell,
but its usefulness outside the tested setting is a methodological proposal,
not an already-proven empirical universal.

## Scoped numerical findings

The numerical evidence is bounded to the audited artifacts: primarily
SQuAD/PubMedQA-style short-answer QA with 7B-class generators, plus fixed
five-dataset threshold summaries, two-dataset cost comparisons, one
second-generator probe, limited retriever checks, and an exploratory
40-question MS-MARCO/QASPER long-form panel. Fixed-output analyses establish
measurement sensitivity, slice-dependent scorer alignment, mixed threshold
transfer, and dataset/weight-dependent deployment trade-offs in these cells.
They do not establish broad generalization to other generators, retrievers,
tasks, languages, judge families, or deployment environments.

## Boundary between the two

The method says what evidence should be disclosed and how to find hidden
degrees of freedom. The experiments demonstrate why that discipline matters
in selected settings. Neither implies that the observed effect sizes or
rankings recur everywhere.

## Rebuttal-ready statement

> Our contribution is a bounded audit methodology, not a universal empirical
> claim about all RAG systems. The tested cells show that scorer input,
> calibration slice, threshold source, and deployment weights can change the
> conclusion. We therefore scope the numerical findings to the reported
> datasets, 7B-class generators, retrievers, fixed outputs, and hardware
> conditions, while presenting the seven-axis protocol as a practical
> disclosure standard whose broader utility should be validated in future
> studies.
