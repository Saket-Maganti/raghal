# Response Length Report

## Result

All six paste fields are below the official NeurIPS 2026 limit of 10,000
characters per review. Each field is pasted separately.

| Field | Characters | Words | Remaining | Editorial target | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Current/initial AC | 3,932 | 515 | 6,068 | 2,700–3,300 | Official pass; target exceeded to retain required acceptance case, evidence hierarchy, two-tier protocol, provenance boundary, citation, and revision commitments |
| `uqxN` | 1,819 | 237 | 8,181 | 1,500–1,900 | Pass |
| `wXNA` | 2,292 | 309 | 7,708 | 2,100–2,500 | Pass |
| `diyB` | 2,276 | 292 | 7,724 | 1,900–2,300 | Pass |
| `d61o` | 2,086 | 289 | 7,914 | 1,700–2,100 | Pass |
| `wh9X` | 2,082 | 267 | 7,918 | 1,800–2,200 | Pass |

The six field bodies total 14,487 characters and 1,909 words. The internal AC
synthesis exactly matches the AC paste body and is also 3,932 characters.
The AC target is an editorial preference, not a scientific or platform gate;
removing the required claim boundaries to meet it would make the response less
complete.

## Counting and synchronization convention

Counts use Unicode code points after trimming leading and trailing whitespace;
internal line breaks count as characters. File headings and package markers
are excluded. Each standalone response body was compared programmatically
with the text between its matching package markers.

## Response mechanics

- Official per-review limit: 10,000 characters.
- OpenReview paste text contains no links.
- No marker text is included in a paste field.
- Manuscript changes are camera-ready commitments, not claims that a revised
  paper or supplement was uploaded during rebuttal.

Status: `PASS_OFFICIAL_2026_LIMIT`.
