# Metric glossary

| Metric | Meaning | Direction |
| --- | --- | --- |
| faithfulness score | 0-100 support score from the pinned judge | higher means more support |
| faithful decision | judge Boolean, required to agree with score threshold 50 | true means classified faithful |
| AP | ranking quality with faithful as positive | higher is better |
| Spearman | rank association with human binary label | higher is better |
| Boolean accuracy | fraction of explicit judge decisions matching humans | higher is better |
| balanced accuracy | mean class recall | higher is better |
| precision | faithful predictions that are human-faithful | higher is better |
| recall | human-faithful rows predicted faithful | higher is better |
| F1 | harmonic mean of precision and recall | higher is better |
| Brier | squared error of score/100 against human label | lower is better |

AP, Spearman, and Boolean accuracy are not interchangeable.
