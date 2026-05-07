# Dataset Cleaning Project

## Project purpose
A Jupyter notebook workflow for exploring a Postgres database, cleaning a
dataset, and producing a documented notebook ready for downstream modelling.
The human drives the process — Claude assists with specific tasks on demand.

## Assumptions
- The Postgres database is already connected in PyCharm's Database tool window
- The Jupyter notebook is open at `notebooks/cleaning.ipynb`
- SQL cells in the notebook are used for querying (PyCharm's `%%sql` cell magic)
- The DataFrame viewer in PyCharm is used for manual visual inspection

---

## Python environment (uv)

This project uses uv. Claude Code's shell sessions are stateless — activating
.venv does not persist between tool calls. Never use `source .venv/bin/activate`
or bare `python` / `pip` commands. Use uv exclusively.

| Task | Command |
|------|---------|
| Run a script | `uv run python script.py` |
| Run pytest | `uv run pytest` |
| Run jupyter | `uv run jupyter notebook` |
| Add a package | `uv add <package>` |
| Sync environment | `uv sync` |
| Check interpreter | `uv run python -c "import sys; print(sys.executable)"` |

Never use `pip install`. Never use `python` directly. Always prefix with `uv run`.

---

## Directory layout

```
dataset-cleaner/
├── CLAUDE.md
├── pyproject.toml               ← uv project file
├── .claude/
│   └── skills/                  ← all three workflow skills
├── notebooks/
│   └── cleaning.ipynb           ← the working notebook
├── data/
│   ├── raw/                     ← original exports (read-only)
│   │   └── profile.json         ← written by workflow 2, read by workflow 3
│   └── output/                  ← cleaned DataFrames saved here
└── configs/
    └── cleaning_config.yaml     ← target column, written by workflow 2
```

---

## Notebook conventions

- SQL cells use `%%sql` magic (SQLAlchemy connection via `ipython-sql`)
- Every transformation code cell must have a markdown cell immediately above it
- Markdown cells explain: what the problem is, why this fix was chosen, rows affected
- Column names use snake_case
- Transformations write to a new variable (e.g. `df_clean`), never in-place
- Raw data loaded into `df_raw` — never modified

---

## Three workflows — invoke by name

### Workflow 1: `explore_db`
**When to use:** You want to understand the database structure and work out what
query to write. Claude will help you explore tables, understand schemas, and
draft a SQL query. You run the query yourself in a SQL cell.

**Trigger:** Type `explore_db` in Claude Code chat.

### Workflow 2: `clean_data`
**When to use:** You have already run a SQL cell to load `df_raw` and have
inspected the data in the DataFrame viewer. Claude will profile the data,
produce a list of issues, and walk through fixes one at a time.

**Trigger:** Type `clean_data` in Claude Code chat.

### Workflow 3: `tidy_notebook`
**When to use:** You have finished cleaning and want Claude to check the
notebook is ordered, documented, and reproducible.

**Trigger:** Type `tidy_notebook` in Claude Code chat.

---

## Fix loop behaviour (used inside `clean_data`)

- Claude presents ONE fix at a time
- Each fix shows: the problem, the recommended treatment, the exact code,
  and the number of rows/values affected
- Claude asks: "Apply this fix? (yes / no / modify: [instruction])"
- Claude does NOT write any notebook cells until receiving explicit approval
- "yes" → write markdown cell + code cell, move to next issue
- "no" → skip, note as deferred
- "modify: [instruction]" → revise the code, show again, re-ask

---

## Database access rules
- Read-only: SELECT queries only
- Never run INSERT, UPDATE, DELETE, DROP, or ALTER via MCP or SQL cells
- Never hardcode credentials — use PyCharm's database connection
