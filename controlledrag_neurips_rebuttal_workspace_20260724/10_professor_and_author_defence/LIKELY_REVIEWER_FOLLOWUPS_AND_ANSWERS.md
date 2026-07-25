# Likely reviewer follow-ups and answers

## Why Qwen2.5-7B rather than a proprietary judge?

The experiment needed an open, immutable, reproducible evaluator that could run under the available two-T4 constraint. Qwen2.5-7B-Instruct was pinned to an exact revision and deterministic decoding. That makes the result auditable and directly addresses whether the submitted finding depends only on older NLI proxies. It does not establish behavior for proprietary judges. ControlledRAG's recommendation is precisely to report judge identity, version, inputs, and calibration rather than treat any one judge as universal.

## Why only 83 determinate human rows?

The 83 rows are the determinate binary subset of the separate typical calibration panel with valid outputs under both judge interfaces. Keeping a same-row complete population avoids comparing interfaces on different cases. The original typical human study had 99 rows and a different label scheme; it is not silently converted into a larger binary population. The 83-row result is therefore bounded calibration evidence. It is paired, reproducible from the frozen private bundle, and not presented as broad human validation.

## Why did the modern judge not reproduce a sign reversal?

A sign reversal was not an inclusion criterion and was never required for the experiment to be informative. Both interfaces rank baseline above HCPC-v1, but the measured contrast changes from 3.32 to 13.94 points. The paired 10.62-point shift has a confidence interval excluding zero. That shows material scorer-input sensitivity under a contemporary judge. The honest conclusion is same ordering with a materially different magnitude, which still affects how strong the system claim appears.

## Was the left-padding repair post-hoc manipulation?

No scientific choice changed. Batched decoder-only generation must begin after each sequence's final prompt token. Right padding caused shorter prompts to generate from padding positions, producing a large interface-specific validity failure. The repair added only `tokenizer.padding_side = "left"`. Model, revision, rows, prompts, rubric, parser, threshold, decoding, batch size, metrics, bootstrap, and inclusion rules stayed frozen. The first run remains excluded, and no outputs from the two runs are combined.

## Why were three outputs excluded?

Each object is valid JSON with score 50 but Boolean faithful set to false. The preregistered rule says score 50 or higher must have faithful true. The strict parser therefore rejects them as threshold inconsistencies. The raw objects are preserved. Exclusion follows the frozen rule and is applied before analysis; it is not selected based on the result. The primary analysis uses the common complete 193-pair intersection and the strong inclusion gate still passes.

## Why not correct the inconsistent Boolean field?

Correcting either the score or Boolean would require guessing which field the judge intended. That would be an outcome-dependent manual recode after the run. The protocol instead treats the entire object as invalid, preserves it, and excludes any analysis cell that needs it. This is stricter and easier to audit. A post-hoc worst-case bound shows that assigning the missing main score anywhere from 0 to 100 would not remove the positive 10.62-point conclusion, but that diagnostic does not alter the primary result.

## Does better human alignment prove correctness?

No. On 83 typical rows and a separate 72-row disagreement-targeted diagnostic slice, context-conditioned scores have higher AP and Spearman. That is direct evidence that context conditioning aligns better with these human labels on these slices. It does not prove universal evaluator correctness, remove annotation uncertainty, or establish performance in other domains. The response states the population, keeps the slices separate, and treats the diagnostic slice as diagnostic.

## Why retain all seven categories?

Each category captures a practical choice that can change a scientific or deployment conclusion: generator, retriever, context structure, scorer, human calibration, threshold transfer, and cost. The categories are not claimed to be unique, exhaustive, or mathematically minimal. Retaining all seven does not require a factorial experiment. Authors disclose every relevant category, then stress-test only alternatives capable of changing the claim. This keeps reporting complete while making experimental effort proportional to claim strength.

## How does the protocol apply beyond short-answer QA?

The procedure can transfer even when the measured numbers cannot. A long-form or agentic study can define its task decision, disclose model and retrieval/tool choices, specify the evidence and evaluator interface, calibrate against deployment-relevant judgments, test threshold or abstention rules, and report cost. It then labels each conclusion Stable, Conditional, or Unresolved. ControlledRAG does not claim that the 10.62-point effect size or the human-slice metrics transfer to those settings.

## Is this a position paper?

The paper proposes a reporting framework, but it also executes a controlled empirical self-audit. The evidence includes a 2,500-row-per-condition scaled analysis, 200 matched pairs, 7,500 fixed rows across scorers, a 600-row input-format analysis, two human slices, threshold transfer, cost, retriever checks, and the new 1,510-request judge run. The contribution is evaluation methodology demonstrated through controlled interventions. The revision will expose that experiment inventory and grade each cell rather than imply uniform breadth.

## How does ControlledRAG differ from a metric benchmark?

A metric benchmark usually ranks evaluators or systems on a fixed task. ControlledRAG asks whether the paper's claim survives reasonable changes in how evaluation is specified. It treats the evaluator identity, input, calibration, threshold, and cost as parts of the scientific claim. The output is a disclosure contract, stress-test plan, evidence grade, and Stable/Conditional/Unresolved decision. Existing benchmarks can supply data or evaluators within this protocol; ControlledRAG is the audit layer around them.

## How does it relate to DRAGged into Conflicts?

Cattan et al. study detecting and addressing conflicts among retrieved sources. ControlledRAG studies how evaluator and reporting choices condition a RAG faithfulness claim. Conflicting evidence is relevant to the retrieval and context categories and may require a claim to remain Conditional or Unresolved. The work is complementary. No contradictory-context experiment was run in this paper, so the citation is used for positioning and decision guidance rather than as empirical support for a new result.

## Can the artifact reproduce every row-level analysis publicly?

No. The public reviewer branch intentionally contains aggregate evidence, canonical estimand code, toy fixtures, tests, manifests, and checksums. Questions, contexts, answers, human annotations, row identifiers, and raw judge outputs remain private. The five-minute public path verifies aggregate claims and mathematical contracts. An independent Level B recomputation was completed from the controlled private bundle without new inference. The artifact states this boundary instead of implying public row-level coverage.

## What private data is withheld and why?

Withheld material includes questions, retrieved evidence, generated answers, row IDs, human annotation rows, rater metadata, raw model text, run ZIPs, and the confidential paper. These files can expose dataset content, annotator information, reviewer material, or local provenance that is inappropriate for an anonymous public release. Aggregate counts and metrics are sufficient for the public verification path. Checksums and controlled private storage preserve the scientific audit trail.

## Did repository cleanup change any result?

No scientific result was recomputed from altered public data. The cleanup removed row-level private material, stale generated packages, legacy experiment drivers, and duplicate runtime code from the reviewer-facing branch. Aggregate result files were preserved, and the new contemporary-judge aggregates come from an independent private recomputation. The release validator checks locked values, checksums, populations, stale AP numbers, privacy, identity, and claim links. Backup refs preserve the complete pre-cleanup state.
