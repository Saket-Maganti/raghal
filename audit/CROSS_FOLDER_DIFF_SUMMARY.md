# Cross-Folder Diff Summary

- `cleanup_20260506_final_code_artifact_cleanup`: 1,674 files, 123,495,124 bytes; 464 source, 74 data, 964 result, 43 paper-classified.
- `deleted_from_head`: 80 files, 7,040,112 bytes; 17 source, 0 data, 0 result, 29 paper-classified.
- `moved_from_repo`: 362 files, 94,457,040 bytes; 84 source, 16 data, 3 result, 173 paper-classified.
- `rag-hallucination-detection_main`: 227 files, 6,722,517 bytes; 125 source, 6 data, 67 result, 7 paper-classified.

Exact duplicates, path conflicts, and folder-unique files are enumerated in `DUPLICATE_FILE_GROUPS.csv`, `RELATIVE_PATH_CONFLICTS.csv`, and `UNIQUE_FILES_BY_FOLDER.csv`.

The cleanup capture contains the broadest experiment/result surface. The submitted artifact is a smaller, clean Git snapshot. The moved and deleted folders preserve omitted packages, logs, and generated state. This audit does not assert that newer timestamps or larger coverage make a remnant scientifically correct.
