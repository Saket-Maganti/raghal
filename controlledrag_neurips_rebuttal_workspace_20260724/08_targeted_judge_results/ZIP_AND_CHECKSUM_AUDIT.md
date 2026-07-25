# ZIP and checksum audit

| Artifact | Located | SHA-256 | Internal manifest |
| --- | --- | --- | --- |
| frozen targeted-judge input ZIP | yes | `1ded9189578cf2af353d58bae073a14ff4e6e064ef485f23dd85c686c721a456` | all 54 listed files pass |
| accepted postprocessed output ZIP | yes | `3e00950596cf982c93030b32e626725a69ac0f4965aef2bca993d0d08e874311` | all 34 listed files pass |
| separately named left-padding repair ZIP | no | unavailable | unavailable |

The accepted package contains the three raw files expected from the repair run, its validation files, model identity, input verification, and left-padding repair lock. The two shards and merged file are record-equivalent: all 1,510 records and request keys match with no duplicates.

The package's strict records and independently parsed records agree on validity and parsed payload for every output.

## Identity boundary

Independent verification completed:

- input ZIP internal checksums;
- output ZIP internal checksums;
- output ZIP SHA-256;
- shard-to-merge record identity;
- raw record preservation within the accepted package.

Not independently verifiable:

- byte or record identity between the missing separately named repair ZIP and the accepted postprocessed ZIP.

Status: `REPAIR_ZIP_NOT_LOCATED_CROSS_ZIP_IDENTITY_UNVERIFIED`.

No substitute ZIP was fabricated.
