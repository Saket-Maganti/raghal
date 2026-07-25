# Estimand and assumption register

| Estimand | Population | Resampling unit | Assumptions | Scope |
| --- | --- | --- | --- | --- |
| answer-only system contrast | 193 complete pairs | pair | fixed outputs; valid strict parse | pinned judge and panel |
| context-conditioned system contrast | same 193 pairs | pair | same | pinned judge and panel |
| difference in contrasts | same 193 pairs | pair | paired interfaces and systems | scorer-input sensitivity |
| AP interface difference | complete rows within each human slice | row | faithful class is positive | ranking alignment |
| Spearman interface difference | same rows | row | finite rank statistic | monotone alignment |
| Boolean accuracy, balanced accuracy, precision, recall, F1 | same rows | none for point estimate | explicit judge Boolean | secondary |
| Brier score | same rows | none for point estimate | score divided by 100 | calibration, lower is better |

Invalid outputs are excluded under the frozen rule. They are not missing request keys and are not imputed.
