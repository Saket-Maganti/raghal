# Privacy Status

Status: `PUSH_BLOCKED_REPOSITORY_PUBLIC`

Authenticated GitHub CLI metadata reports the target repository visibility as
`PUBLIC`. Under the prompt's privacy rules:

- no rebuttal material may be pushed;
- exact confidential review text may not be committed;
- reviewer concerns must be stored only as sanitized paraphrases;
- branch work may be committed locally;
- no remote branch URL will be created.

The remote owner is redacted from committed logs. No external rater identity,
personal absolute path, local username, credential, token, or environment file
may enter the commit.

This status remains in force unless a later authenticated check establishes a
different repository or a private remote specifically authorized for the
rebuttal.
