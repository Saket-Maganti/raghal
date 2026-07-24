# Human Evaluation Codebook: Faithfulness

## Label Definitions

### 1. Faithful
**Criteria:** Every factual claim in the generated answer is supported by the retrieved context.
- **Example:**
  - *Context:* "The Eiffel Tower was completed in 1889."
  - *Answer:* "The Eiffel Tower was finished in 1889."
  - *Result:* Faithful.
- **Example (Minor rephrasing):**
  - *Context:* "Water boils at 100 degrees Celsius at sea level."
  - *Answer:* "At sea level, the boiling point of water is 100°C."
  - *Result:* Faithful.

### 2. Hallucinated
**Criteria:** At least one factual claim in the generated answer is unsupported or contradicted by the retrieved context.
- **Sub-type: Contradiction**
  - *Context:* "The sun is 93 million miles away."
  - *Answer:* "The sun is 10 million miles away."
- **Sub-type: Unsupported (Out-of-context info)**
  - *Context:* "Jupiter is the largest planet."
  - *Answer:* "Jupiter is the largest planet and it has 95 moons." (The number of moons is correct in reality, but not in the context).
- **Sub-type: Entity Swap**
  - *Context:* "Alice went to Paris. Bob went to London."
  - *Answer:* "Alice went to London."

### 3. Unclear
**Criteria:** The context or answer is too ambiguous, incomplete, or underspecified for a reliable binary decision.
- **Example:**
  - *Context:* "He was born in 1990." (No indication of who 'He' is).
  - *Answer:* "The author was born in 1990."
- **Example:**
  - *Context:* "The stock price rose."
  - *Answer:* "The stock price increased significantly." (Is 'significantly' supported?).

## Decision Workflow
1. Read the Question and the Answer.
2. Break the Answer into individual factual claims.
3. For each claim, search the Context for supporting evidence.
4. If ALL claims are supported -> **Faithful**.
5. If ANY claim is contradicted or NOT mentioned in the context -> **Hallucinated**.
6. If the context is missing, corrupted, or the mapping is impossible -> **Unclear**.
