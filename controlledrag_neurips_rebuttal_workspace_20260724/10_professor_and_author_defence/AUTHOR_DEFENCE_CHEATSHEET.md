# Author defence cheatsheet

1. **Why 193, not 194?** One preregistered pair lacks four valid required cells because a context-conditioned output violates the frozen threshold rule. The same 193 complete pairs are used everywhere in the main analysis.
2. **How is 3.32 calculated?** On each pair, subtract HCPC-v1's answer-only score from baseline's answer-only score, then average the 193 paired differences.
3. **How is 13.94 calculated?** Repeat the same paired subtraction using context-conditioned scores.
4. **Why 10.62?** Subtract the answer-only contrast, 3.316, from the context-conditioned contrast, 13.938.
5. **Why paired?** The systems and interfaces are compared on the same fixed cases. Pairing removes case-mix variation.
6. **AP versus Spearman?** AP measures faithful-positive ranking quality. Spearman measures monotone rank association with the human label.
7. **Why is Brier lower-is-better?** It is squared probability error after scaling the score to `[0,1]`.
8. **Why exclude three outputs?** They contradict the preregistered Boolean-threshold rule. Changing them after seeing results would alter the protocol.
9. **Why useful without sign reversal?** Ordering stays the same, but the measured effect becomes more than four times larger. That still changes how strong the claim appears.
10. **Why keep 83 and 72 separate?** The 83-row slice is typical determinate calibration. The 72-row slice was targeted for disagreement and is diagnostic.
11. **Stable, Conditional, Unresolved?** Stable survives audited alternatives; Conditional depends materially on a plausible choice; Unresolved lacks adjudicating evidence.
12. **Why not test every seven-category combination?** Disclose all relevant categories, then stress-test only claim-critical alternatives.
13. **Why is left padding technical?** Decoder-only batches must generate from each prompt's final token. Left padding fixes that position without changing any scientific input or decision.
14. **What remains out of scope?** Universal evaluator correctness, proprietary judges, arbitrary agents, broad long-form claims, and contradictory-context effects.
