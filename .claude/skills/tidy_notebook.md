---
name: tidy_notebook
description: >
  Workflow 3. Final quality check on the Jupyter notebook. Re-executes it
  top to bottom, removes empty/unused cells, verifies every transformation
  is documented, and confirms the notebook is reproducible.
version: 1.0.0
trigger: "tidy_notebook"
---

# Workflow 3: `tidy_notebook`

## Purpose
You've finished cleaning. This workflow checks the notebook is clean,
ordered, reproducible, and fully documented before you hand it off.

---

## Step 1 — Re-execute the notebook top to bottom

Run in the terminal (not as a notebook cell):

```bash
uv run jupyter nbconvert --to notebook --execute \
  --ExecutePreprocessor.timeout=300 \
  --ExecutePreprocessor.kernel_name=python3 \
  notebooks/cleaning.ipynb \
  --output notebooks/cleaning_executed.ipynb
```

Note: always use `uv run jupyter` — never bare `jupyter`. This ensures the
correct environment is used.

**If execution fails:**
Report which cell failed and the error message, then ask:
"Cell [N] failed with: [error]. Would you like me to fix it?
(yes / show me the cell / skip)"

Do not proceed until all cells run successfully, or the user explicitly
asks to skip execution verification.

**If execution succeeds:** Report "All [N] cells ran successfully in order."

---

## Step 2 — Check cell execution order

Examine the executed notebook's cell execution counts. They should run
1, 2, 3, ... without gaps or out-of-order numbers.

If out of order: note this but treat it as resolved by Step 1's clean
re-execution (the executed output notebook has correct order).

---

## Step 3 — Check for undocumented transformations

Use the PyCharm MCP tool `get_file_text_by_path` to read
`notebooks/cleaning.ipynb`. Scan every code cell. For each code cell that
contains any of these patterns:

- `df_clean =`
- `.drop(`
- `.fillna(`
- `.astype(`
- `pd.to_numeric`
- `pd.to_datetime`
- `drop_duplicates`
- `KNNImputer` / `IterativeImputer`
- `winsorize`
- `np.log1p`

Confirm there is a markdown cell immediately before it.

For any transformation cell missing a markdown explanation, add a placeholder:

```markdown
### [Transformation — please review]

<!-- Auto-generated placeholder. Please describe:
     - What problem this addresses
     - Why this method was chosen
     - Rows/values affected -->
```

Report: "Found [N] transformation cells missing documentation. Added [N]
placeholder cells — please fill them in."

---

## Step 4 — Find and propose deletion of unused cells

Identify:
- **Empty code cells** — no content at all
- **Cells with no output** that contain only `print(df.head())`,
  `df.shape`, `df.dtypes` or similar one-line exploratory calls
  that aren't preceded by a markdown explaining why they're there

Present a list:
"I found [N] cells that appear unused or empty:
  Cell [N]: [first line or 'empty']
  ...

Delete all of them? (yes / show me each one / no)"

If "show me each one": present one at a time and ask "Delete? (yes / no)".

---

## Step 5 — Verify the cleaning summary exists

Check that the cleaning decisions summary table (written at the end of
`clean_data`) is present and covers all the transformations in the notebook.

If any transformation is in the code but missing from the summary, add it.

---

## Step 6 — Check placeholder cells remain

If any markdown cells contain `<!-- Auto-generated placeholder -->`,
flag them explicitly:

"There are [N] placeholder markdown cells that need your attention before
this notebook is final:
  [list the cell headings]"

---

## Step 7 — Verify the save cell exists and ran

Confirm a cell exists that saves `data/output/cleaned.parquet` and that
it ran successfully in Step 1's execution.

If missing, add it:

```python
from pathlib import Path
Path("data/output").mkdir(parents=True, exist_ok=True)
df_clean.to_parquet("data/output/cleaned.parquet", index=False)
print(f"Saved: {df_clean.shape[0]:,} rows × {df_clean.shape[1]} columns")
```

---

## Step 8 — Write the sign-off cell

Add a markdown cell at the very end of the notebook:

```markdown
## Notebook QA sign-off

- Re-executed top-to-bottom: ✓
- All cells produce expected output: ✓
- All transformations documented: ✓  *(or: N placeholders remain)*
- Empty/unused cells removed: ✓
- Cleaned data saved to: `data/output/cleaned.parquet`

---
*Reviewed: [date] — fill in your name before committing.*
```

---

## Step 9 — Final report to the user

"The notebook is clean. Summary:

- Original: [N] rows × [M] columns
- Final: [N'] rows × [M'] columns
- Fixes applied: [list each in one line]
- Deferred issues: [list if any]
- Placeholder cells remaining: [N — needs manual fill-in, or 'none']
- Output: data/output/cleaned.parquet

To reproduce from scratch: restart the kernel and run all cells."
