# Findings

One file per investigation. The point is that understanding accumulates in the
repository instead of evaporating in a chat log.

Each finding states the question, the answer, what it assumed, and which script
in `analysis/` reproduces it. If a finding cannot be reproduced by running one
command, it is not a finding yet.

| Finding | Question | Script |
|---|---|---|
| [staging-split.md](staging-split.md) | Where should a two-stage rocket separate, and what does getting it wrong cost? | `analysis/staging_split.py` |
