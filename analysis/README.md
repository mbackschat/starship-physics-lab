# Analysis scripts

One script per question. Each is committed, re-runnable, and imports the same
tested physics core the web app uses, so an answer here and an answer there can
never disagree.

## Running

```sh
uv run python analysis/staging_split.py
```

Output lands in `analysis/out/` and is gitignored. Regenerate rather than commit.

## Writing a new one

```python
"""One sentence saying which question this answers.

Run:  uv run python analysis/my_question.py
Out:  analysis/out/my-question.{png,html,md,csv}
"""

from labbook import Col, Quantity, save_figure, save_table, table
from labbook.units import METRIC          # swap for US to get the same report in pounds
from rocketry.library import load
from rocketry.vehicle import analyse

lib = load()
rows = [analyse(lib, key) for key in ("starship_v3", "falcon9_droneship")]

report = table(rows, [
    Col("name", "Vehicle"),
    Col("total_delta_v", "Ideal Δv", Quantity.VELOCITY),
    Col("payload_t", "Payload", Quantity.MASS, digits=1),
], formatter=METRIC, title="My question")

print(report)
save_table(report, "my-question")
```

## Conventions

- **Never hard-code a rocket.** Load it from `data/`. If a number is missing,
  add it to the library with its provenance rather than inlining it here.
- **Print the table.** The script should be readable in a terminal or a chat
  without opening a file.
- **Say what is assumed.** A script that silently picks an Isp is a script whose
  answer cannot be trusted six months later.
- **Write up anything worth keeping** in `docs/findings/`, linking back to the
  script. The script is the method; the finding is the conclusion.
