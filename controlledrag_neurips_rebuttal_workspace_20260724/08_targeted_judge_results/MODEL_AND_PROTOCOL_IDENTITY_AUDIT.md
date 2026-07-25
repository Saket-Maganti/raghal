# Model and protocol identity audit

Verified on all 1,510 accepted-run records:

| Field | Locked value | Result |
| --- | --- | --- |
| model | `Qwen/Qwen2.5-7B-Instruct` | pass |
| revision | `a09a35458c702b33eeacc393d103063234e8bc28` | pass |
| quantization | bitsandbytes NF4 4-bit | pass |
| compute dtype | float16 | pass |
| double quantization | true | pass |
| sampling | false | pass |
| temperature | 0.0 | pass |
| top-p | 1.0 | pass |
| max new tokens | 96 | pass |
| batch size per GPU | 4 | pass |
| repair | decoder-only left padding only | pass |

There are zero identity mismatches. The input verification receipt reports zero real rows scored during preflight and zero network inference calls. Prompt B performed no inference, model loading, or API call.

Protocol status: `MODEL_AND_PROTOCOL_IDENTITY_PASS`.
