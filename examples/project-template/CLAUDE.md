# Remote-First Session Protocol

- **BEGIN:** identify the project and current Git branch; only work within this VPS workspace.
- **EXECUTE:** create code, documents and artifacts inside this repository. Do not put outputs in the home directory.
- **VALIDATE:** run relevant tests and state failures clearly.
- **CHECKPOINT:** the Stop hook handles eligible commits on `agent/*`. Do not push automatically.
- **PUBLISH:** Syncthing replicates ordinary files to a receive-only laptop mirror; never claim delivery without checking Syncthing.
- **REPORT:** summarize changed paths, tests, Git commit (if present) and any unfinished work.
- **SECURITY:** never commit credentials, tokens, `.env`, private keys, user transcripts or secrets. Require human review before publishing.

This file defines behavior, not permissions. Hook scripts enforce only the limited checks implemented in them.
