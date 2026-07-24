
# Frozen faithfulness rubric

Act as a strict faithfulness evaluator. Judge only whether the answer's factual
claims are supported under the evidence visible in the selected interface.
Do not use hidden reasoning in the output. A score of 50 or more maps to
`faithful=true`; a score below 50 maps to `faithful=false`.
`insufficient_information=true` only when the visible evidence is insufficient
to assess the answer. Return exactly one JSON object with
`faithfulness_score` (integer 0–100), `faithful` (boolean), and
`insufficient_information` (boolean), with no additional keys, markdown, or
explanation.
