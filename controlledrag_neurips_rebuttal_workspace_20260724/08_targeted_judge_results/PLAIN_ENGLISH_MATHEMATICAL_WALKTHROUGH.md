# Plain-English mathematical walkthrough

For each of the 193 complete pairs, subtract the HCPC-v1 score from the baseline score. Average those paired differences once for answer-only judging and once for context-conditioned judging.

The answer-only average difference is 3.32 points. The context-conditioned average difference is 13.94 points.

Subtract 3.32 from 13.94. The result is 10.62 points. That is the scorer-input sensitivity estimate.

Both 3.32 and 13.94 are positive, so the system ordering stays the same. The magnitude changes materially.

Bootstrap resampling repeats the calculation on sampled pair IDs to describe uncertainty. The displayed 10.62 is still the direct calculation on all 193 pairs, not the mean of bootstrap calculations.
