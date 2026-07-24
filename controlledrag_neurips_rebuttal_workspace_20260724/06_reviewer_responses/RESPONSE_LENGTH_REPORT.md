# Response Length Report

## Result

All six recommended paste fields are below the official NeurIPS 2026
10,000-character per-review limit. The fields are pasted separately: one
response to the current/initial AC note and one response for each of the five
reviewers.

| Field | Characters | Words | Remaining under 10,000 |
| --- | ---: | ---: | ---: |
| Current/initial AC | 3,144 | 425 | 6,856 |
| `uqxN` | 1,795 | 253 | 8,205 |
| `wXNA` | 1,899 | 265 | 8,101 |
| `diyB` | 2,047 | 278 | 7,953 |
| `d61o` | 1,732 | 235 | 8,268 |
| `wh9X` | 2,602 | 346 | 7,398 |

The six field bodies total 13,219 characters, but they are not one response
field. The internal AC synthesis is 3,047 characters. The optional
modern-judge Version B insertion is 345 characters and is marked unusable
because no real run exists.

## Counting convention

Counts use Unicode code points after removing leading and trailing whitespace;
internal line breaks count as characters. Markdown body text is counted, but
file headings and package control markers are excluded. The bodies in
`FINAL_OPENREVIEW_PASTE_PACKAGE.md` were checked text-for-text against the
corresponding response-file bodies.

## Official rule

The NeurIPS 2026 Main Track Handbook states a 10,000-character limit for each
per-review rebuttal, permits OpenReview Markdown, prohibits links in response
text, and does not permit a revised paper or supplement during rebuttal. The
E&D track follows the main-track response process. The current package uses
no links and frames manuscript changes as camera-ready updates if accepted.

Status: `PASS_OFFICIAL_2026_LIMIT`.
