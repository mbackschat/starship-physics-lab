# Studies

One folder per question. Each holds the script that answers it, the written
conclusion, and the figures the script generated. Method and result sit
together, so a conclusion is never separated from the code that produced it.

```
studies/<name>/
  run.py        the script. imports the same physics core the web app uses
  finding.md    the conclusion: question, answer, assumptions, how to reproduce
  out/          generated figures, tables and data. gitignored, regenerate freely
```

If a finding cannot be reproduced by running one command, it is not a finding yet.

| Study | Question | Answer |
|---|---|---|
| [staging-split](staging-split/finding.md) | Where should a two-stage rocket separate, and what does getting it wrong cost? | A factor of 2.2 in payload |
| [article-verification](article-verification/finding.md) | Do the source article's numbers hold up? | 61 of 64 reproduce; 3 errors found |
| [v4-scaling](v4-scaling/finding.md) | Does making Starship's ship bigger in V4 help? | No, and the size of the harm turns on one assumption |
| [flight-14-prediction](flight-14-prediction/finding.md) | What will Flight 14 deliver to orbit? | 296 to 298 t total, whatever the ship weighs. **Pre-registered before the flight.** |
| [fleet-comparison](fleet-comparison/finding.md) | How does every rocket in the library compare, once flown? | 5 of 13 are modelled as they fly, and those land within 12 % |

A study may also be written *before* the answer is knowable. A prediction committed
ahead of the measurement is the only kind that can be checked honestly afterwards,
so it is marked as pre-registered and never edited once the data arrives.

## Running

```sh
uv run python studies/staging-split/run.py
```

Output lands in that study's `out/`, which is gitignored. Regenerate rather than commit.

## Writing a new one

Create `studies/<name>/run.py`:

```python
"""One sentence saying which question this answers.

Run:  uv run python studies/my-question/run.py
Out:  studies/my-question/out/my-question.{png,html,md,csv}
"""

from labbook import Col, Quantity, beside, save_figure, save_table, table
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
save_table(report, "my-question", out_dir=beside(__file__))
```

Then write `finding.md` beside it and add a row to the table above.

## Conventions

- **Never hard-code a rocket.** Load it from `data/`. If a number is missing, add
  it to the library with its provenance rather than inlining it here.
- **Print the table.** The script should be readable in a terminal or a chat
  without opening a file.
- **Say what is assumed.** A script that silently picks an Isp is a script whose
  answer cannot be trusted six months later. Every `finding.md` has an
  assumptions section, and it is the section that matters most.
- **Write output with `beside(__file__)`**, so it lands in this study's `out/`.
