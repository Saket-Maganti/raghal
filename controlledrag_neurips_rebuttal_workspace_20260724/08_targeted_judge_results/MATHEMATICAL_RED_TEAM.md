# Mathematical red team

| Attack | Result |
| --- | --- |
| reverse baseline-HCPC sign | caught by toy and locked-result tests |
| compare different pair sets | prevented by common-intersection assertion |
| use bootstrap mean as point estimate | corrected |
| use seed offsets | corrected |
| pool human slices | prohibited and tested by population receipt |
| silently retain NaN Spearman point estimate | corrected to direct observed value |
| replace invalid score 50 Boolean | prohibited by strict parser |
| change positive class | locked to faithful `1` |
| treat Brier as higher-is-better | metric glossary rejects |
| infer modern sign reversal | rejected because both contrasts are positive |
| claim universal human superiority | rejected by claim boundary |
| let one pair determine result | leave-one-pair-out range remains positive |

Status: `MATHEMATICAL_AUDIT_PASS_WITH_CLARIFICATIONS`.
