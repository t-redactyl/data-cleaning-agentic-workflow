---
name: clean_data
description: >
  Demo workflow. Reads audit results from Jupyter runtime variables if already
  present, otherwise runs the audit cell once. Presents issues and first fix
  immediately. Target hardcoded as 'income'.
version: 4.0.0
trigger: "clean_data"
---

# Workflow 2: `clean_data`

## Hardcoded configuration
- Target column: `income`
- Issue types: missingness, outliers, duplicates ONLY

---

## On startup — check runtime variables FIRST

Read the `NotebookRuntimeVariablesRetrieverSource` attachment immediately.

### If `issues_df` is present in the runtime variables:
The audit has already been run. Do NOT execute any cells.
Read the issues directly from the attachment:
- `issues_df` contains the ranked issue list
- `missing_df` contains the missingness summary
- `n_dup` contains the duplicate count
- `df_raw` shape is available from the attachment

Go directly to **Step 2** — present the issue list and first fix immediately.

### If `issues_df` is NOT present in the runtime variables:
Run the audit cell in **Step 1** once, then go to **Step 2**.

### If `df_clean` is present in the runtime variables:
The workflow has already been partially completed in a previous session.
Tell the user: "It looks like cleaning is already in progress — df_clean
exists with [shape]. Would you like to continue from where you left off,
or start fresh? (continue / restart)"

---

## Step 1 — Audit cell (only if issues_df not already in runtime)

Write and execute once:

```python
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import json, yaml

TARGET_COL = "income"
df_features = df_raw.drop(columns=[TARGET_COL])
df_clean = df_raw.copy()

issues = []

for col in df_features.columns:
    n = df_features[col].isnull().sum()
    if n > 0:
        pct = n / len(df_features) * 100
        issues.append({
            "type": "missingness", "column": col,
            "detail": f"{n:,} missing ({pct:.1f}%)",
            "severity": "high" if pct > 30 else "medium" if pct > 5 else "low"
        })

for col in df_features.select_dtypes(include=[np.number]).columns:
    s = df_features[col].dropna()
    if len(s) < 10: continue
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    n_iqr = int(((s < q1 - 3*iqr) | (s > q3 + 3*iqr)).sum())
    n_z   = int((np.abs(stats.zscore(s)) > 3).sum())
    if n_iqr > 0 or n_z > 0:
        issues.append({
            "type": "outlier", "column": col,
            "detail": f"IQR outliers: {n_iqr:,} | z-score outliers: {n_z:,}",
            "severity": "high" if max(n_iqr, n_z) / len(s) > 0.05 else "low"
        })

n_dup = int(df_features.duplicated().sum())
if n_dup > 0:
    issues.append({
        "type": "duplicates", "column": "ALL",
        "detail": f"{n_dup:,} exact duplicate rows ({n_dup/len(df_features)*100:.1f}%)",
        "severity": "high" if n_dup / len(df_features) > 0.01 else "low"
    })

sev_order = {"high": 0, "medium": 1, "low": 2}
issues_df = (pd.DataFrame(issues)
    .assign(_o=lambda d: d["severity"].map(sev_order))
    .sort_values("_o").drop(columns="_o")
    .reset_index(drop=True))
issues_df.index += 1

print(f"Shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} cols | target: {TARGET_COL}")
print(f"Issues: {len(issues)}  (high: {sum(1 for i in issues if i['severity']=='high')}  "
      f"medium: {sum(1 for i in issues if i['severity']=='medium')}  "
      f"low: {sum(1 for i in issues if i['severity']=='low')})")
print(f"\n{issues_df.to_string()}")

Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("configs").mkdir(exist_ok=True)
json.dump({"shape": list(df_raw.shape),
           "dtypes": df_raw.dtypes.astype(str).to_dict(),
           "missing": df_raw.isnull().sum().to_dict(),
           "missing_pct": (df_raw.isnull().mean() * 100).round(2).to_dict(),
           "nunique": df_raw.nunique().to_dict()},
          open("data/raw/profile.json", "w"), default=str, indent=2)
yaml.dump({"target_column": TARGET_COL,
           "n_rows": int(df_raw.shape[0]),
           "n_cols": int(df_raw.shape[1])},
          open("configs/cleaning_config.yaml", "w"))
```

---

## Step 2 — Present issue list and first fix in ONE message

Whether issues came from the runtime attachment or from the audit cell,
present them immediately in this format — no preamble, no confirmation:

```
Found [N] issues ([X] high, [Y] medium, [Z] low).

[paste issues_df as a table]

**Issue 1/N — [severity] — [type]: `[column]`**
[detail]

[proposed fix from the matching template below]

Apply this fix? (yes / no / modify: [instruction])
```

Also write this initialisation cell in the notebook before the first fix
(only if df_clean is not already in the kernel):

```python
df_clean = df_raw.copy()
```

---

## Fix templates

### Missingness

Determine mechanism from data already in memory — no new cell needed:
- Compute point-biserial correlation between missingness indicator and
  numeric columns using values already available in the runtime variables

| Condition | Fix |
|-----------|-----|
| < 1% | Fill: numeric → mean, categorical → mode |
| 1–30%, MCAR | KNN imputation (k=5) |
| 1–30%, MAR | Iterative imputation |
| Possible MNAR | Indicator column + median fill |
| > 30% | Drop column |

**Markdown cell:**
```markdown
### Missingness: `<col>`
- Missing: <N> (<X>%)  |  Mechanism: <MCAR/MAR/MNAR>
- Fix: <method>  |  Rationale: <one sentence>
```

**Code cell:**
```python
# Missingness: <col>
print(f"Before: {df_clean['<col>'].isnull().sum()} missing")
<fix code>
print(f"After:  {df_clean['<col>'].isnull().sum()} missing")
```

### Outliers

Ask ONE question only:
"Are the outliers in `<col>` data errors (a) or genuine extremes (b)?"

| Answer | Fix |
|--------|-----|
| a | Remove rows outside IQR 3× fence |
| b | skew > 1.0 → log1p transform; skew ≤ 1.0 → Winsorize 1/99th pct |

**Markdown cell:**
```markdown
### Outliers: `<col>`
- Outliers: <N> (<X>%)  |  Interpretation: <error/genuine>
- Fix: <method>  |  Affected: <N> rows
```

**Code cell:**
```python
# Outliers: <col>
print(f"Before: min={df_clean['<col>'].min():.4g}, max={df_clean['<col>'].max():.4g}, n={len(df_clean)}")
<fix code>
print(f"After:  min={df_clean['<col>'].min():.4g}, max={df_clean['<col>'].max():.4g}, n={len(df_clean)}")
```

### Duplicates

No question — propose immediately:

```
Fix: Drop exact duplicates, keep first. Removes <N> rows → <N_remaining> remaining.

  df_clean = df_clean.drop_duplicates(keep="first").reset_index(drop=True)
```

**Markdown cell:**
```markdown
### Duplicates
- Exact duplicates: <N> rows (<X>%)
- Fix: Drop duplicates, keep first occurrence
```

**Code cell:**
```python
# Duplicates
print(f"Before: {len(df_clean):,} rows")
df_clean = df_clean.drop_duplicates(keep="first").reset_index(drop=True)
print(f"After:  {len(df_clean):,} rows")
```

---

## Step 3 — After each approval

Combine confirmation and next issue in ONE message:

```
✓ Applied. (<N> issues remaining)

**Issue X/N — [severity] — [type]: `[column]`**
[detail + proposed fix]

Apply this fix? (yes / no / modify: [instruction])
```

Never send a standalone confirmation without the next issue.

---

## Step 4 — Final cell

```python
from pathlib import Path
Path("data/output").mkdir(parents=True, exist_ok=True)
df_clean.to_parquet("data/output/cleaned.parquet", index=False)
print(f"Saved → data/output/cleaned.parquet")
print(f"Shape: {df_raw.shape} → {df_clean.shape}")
nulls = df_clean.isnull().sum()
print(f"Remaining nulls:\n{nulls[nulls > 0].to_string() or 'None'}")
```

Write a single markdown summary cell, then tell the user:
"Done. Type `tidy_notebook` for the final check."
