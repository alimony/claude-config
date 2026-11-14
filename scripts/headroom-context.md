## Compressed tool output

Tool output may pass through a local Headroom proxy that shortens it. It can cut content from Bash output. It never cuts a fresh Read, Grep or Edit result, but it can swap lines you already have for a pointer to the earlier copy.

- When the exact content of a file matters, read it with Read, not with `cat`, `sed` or `head` through Bash.
- `[↑NL same as msg M: '…']` replaces N lines that appear earlier in the conversation. Find them there by the quoted first line. A `+dL` or `-dL` after M means their line numbers moved by d.
- `<<ccr:…>>`, `Retrieve more: hash=…` and `Retrieve original: hash=…` mark removed content. Before you rely on it, call `headroom_retrieve` with the hash as the only tool call in that turn, because the proxy answers a retrieval only when it is alone. If retrieval fails, re-run the original command.
- `[Read content stale: …]` replaces an earlier Read of a file that has changed since. Read the file again instead of retrieving the old copy.
