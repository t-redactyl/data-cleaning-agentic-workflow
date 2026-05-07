---
name: clean_data
description: >
  Workflow 2. Profiles df_raw, scans for issues, and walks through fixes
  one at a time with user approval before writing each notebook cell.
version: 2.0.0
trigger: "clean_data"
---

# Workflow 2: `clean_data`

## On startup — read before doing anything

Before writing any code or asking any questions, check the current message
context for a `NotebookRuntimeVariablesRetrieverSource` attachment. PyCharm
attaches Jupyter runtime variables automatically. This attachment will show
the names, types, and column lists of all DataFrames currently in the kernel.

If a runtime variables attachment is present:
- Identify which DataFrame is `df_raw` from the attachment
- Read its column list directly from the attachment — do NOT run a cell to
  check this
- Proceed immediately to the target question (Step 2), skipping Step 1

If no attachment is present:
- Run Step 1 to confirm df_raw exists

---

## Step 1 — Confirm df_raw (only if no runtime attachment)

Run one cell only:

```python
print(list(df_raw.columns))
print(f"{df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")
```

If this raises NameError, stop and tell the user:
"Please run your SQL cell to load df_raw first, then type `clean_data` again."

---

## Step 2 — Ask for the target (one question, no waiting for confirmation)

Using the column list already in context (from the attachment or Step 1),
ask in a single message:

"df_raw is loaded with [N] rows and these columns:
  [list columns]

Which column is your model target (the one you'll be predicting)?
Type the column name, or 'none'."

Wait for one response. Accept the column name directly — do not ask for
confirmation. If the column name doesn't match, show the list again and
re-ask once.

---

## Step 3 — Run profile AND audit in a single cell

Do not write separate cells for profiling and auditing. Combine everything
into ONE cell that runs once and produces the complete issue list.

Write and execute:

```python
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import json, yaml

TARGET_COL = "<confirmed_target_or_None>"

# ── Separate features ────────────────────────────────────────────────────────
if TARGET_COL:
    df_features = df_raw.drop(columns=[TARGET_COL])
else:
    df_features = df_raw.copy()

# ── Profile ──────────────────────────────────────────────────────────────────
missing = df_raw.isnull().sum()
missing_pct = (missing / len(df_raw) * 100).round(2)
missing_df = pd.DataFrame({"count": missing, "pct": missing_pct}).query("count > 0")

print(f"Shape: {df_raw.shape[0]:,} rows × {df_raw.shape[1]} columns")
print(f"Target: {TARGET_COL}")
print(f"\nMissing values:\n{missing_df.sort_values('pct', ascending=False).to_string() if len(missing_df) else 'None'}")
print(f"\nDtypes:\n{df_raw.dtypes.to_string()}")

# ── Audit ─────────────────────────────────────────────────────────────────────
issues = []

for col in df_features.columns:
    n_miss = df_features[col].isnull().sum()
    if n_miss > 0:
        pct = n_miss / len(df_features) * 100
        issues.append({"type": "missingness", "column": col,
            "detail": f"{n_miss:,} missing ({pct:.1f}%)",
            "severity": "high" if pct > 30 else "medium" if pct > 5 else "low"})

for col in df_features.select_dtypes(include="object").columns:
    n_non_null = df_features[col].notnull().sum()
    coerced_n = pd.to_numeric(df_features[col], errors="coerce").notnull().sum()
    if coerced_n / max(n_non_null, 1) > 0.8:
        issues.append({"type": "type_consistency", "column": col,
            "detail": f"Looks numeric but stored as object ({coerced_n:,}/{n_non_null:,} coercible)",
            "severity": "medium"})
    if any(kw in col.lower() for kw in ["date","time","dt","year","month"]):
        dt_n = pd.to_datetime(df_features[col], errors="coerce").notnull().sum()
        if dt_n / max(n_non_null, 1) > 0.8:
            issues.append({"type": "type_consistency", "column": col,
                "detail": "Date column stored as object",
                "severity": "medium"})

for col in df_features.select_dtypes(include=[np.number]).columns:
    s = df_features[col].dropna()
    if len(s) < 10: continue
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    n_iqr = ((s < q1 - 3*iqr) | (s > q3 + 3*iqr)).sum()
    n_z   = (np.abs(stats.zscore(s)) > 3).sum()
    if n_iqr > 0 or n_z > 0:
        issues.append({"type": "outlier", "column": col,
            "detail": f"IQR outliers: {n_iqr:,} | z-score: {n_z:,}",
            "severity": "high" if max(n_iqr,n_z)/len(s) > 0.05 else "low"})

n_dup = df_features.duplicated().sum()
if n_dup > 0:
    issues.append({"type": "duplicates", "column": "ALL",
        "detail": f"{n_dup:,} exact duplicate rows ({n_dup/len(df_features)*100:.1f}%)",
        "severity": "high" if n_dup/len(df_features) > 0.01 else "low"})

if TARGET_COL:
    for col in df_features.select_dtypes(include=[np.number]).columns:
        try:
            corr = df_features[col].corr(df_raw[TARGET_COL])
            if abs(corr) > 0.95:
                issues.append({"type": "leakage", "column": col,
                    "detail": f"Correlation with target = {corr:.3f}",
                    "severity": "high"})
        except: pass
    for col in df_features.columns:
        if df_features[col].nunique() == len(df_features):
            issues.append({"type": "leakage", "column": col,
                "detail": "Cardinality = n_rows — likely an ID column",
                "severity": "medium"})

for col in df_features.columns:
    if df_features[col].nunique() <= 1:
        issues.append({"type": "type_consistency", "column": col,
            "detail": "Constant column", "severity": "medium"})

# ── Sort and display ──────────────────────────────────────────────────────────
sev = {"high": 0, "medium": 1, "low": 2}
issues_df = pd.DataFrame(issues)
if len(issues_df):
    issues_df = (issues_df
        .assign(_o=issues_df["severity"].map(sev))
        .sort_values("_o").drop(columns="_o")
        .reset_index(drop=True))
    issues_df.index += 1

print(f"\n{'='*60}")
print(f"ISSUES FOUND: {len(issues)} "
      f"(high: {sum(1 for i in issues if i['severity']=='high')}, "
      f"medium: {sum(1 for i in issues if i['severity']=='medium')}, "
      f"low: {sum(1 for i in issues if i['severity']=='low')})")
print(f"{'='*60}")
print(issues_df.to_string())

# ── Save profile and config ───────────────────────────────────────────────────
Path("data/raw").mkdir(parents=True, exist_ok=True)
Path("configs").mkdir(exist_ok=True)

json.dump({
    "shape": list(df_raw.shape),
    "dtypes": df_raw.dtypes.astype(str).to_dict(),
    "missing": missing.to_dict(),
    "missing_pct": missing_pct.to_dict(),
    "nunique": df_raw.nunique().to_dict(),
}, open("data/raw/profile.json","w"), default=str, indent=2)

yaml.dump({
    "target_column": TARGET_COL,
    "n_rows": int(df_raw.shape[0]),
    "n_cols": int(df_raw.shape[1]),
}, open("configs/cleaning_config.yaml","w"))

# Make issues available for the fix loop
print("\nReady to fix issues.")
```

---

## Step 4 — Present the issue list and start immediately

After the cell runs, present the issues table in chat (do not ask "ready to
start?" — just begin with issue #1 immediately):

"Found [N] issues. Starting with the highest severity:

**Issue 1/N — [type]: [column]**
[detail from issues_df]

[proposed fix from the matching specialist skill]

Apply this fix? (yes / no / modify: [instruction])"

This means the first fix proposal appears in the SAME message as the issue
list. The user sees results and a decision to make in one turn.

---

## Step 5 — Fix loop

Initialise before the loop:
```python
df_clean = df_raw.copy()
```

For each issue, invoke the matching specialist skill inline — do not send a
separate message just to announce which skill is being used:

| type             | skill                 |
|------------------|-----------------------|
| missingness      | `$missingness`        |
| type_consistency | `$type-consistency`   |
| outlier          | `$outlier-detection`  |
| duplicates       | `$duplicate-detection`|
| leakage          | `$feature-leakage`    |

After each approval, immediately present the next issue without a
confirmation message in between. Pattern:

```
[User: yes]
✓ Fix applied. (N-1 issues remaining)

**Issue X/N — [type]: [column]**
...proposed fix...

Apply this fix? (yes / no / modify: [instruction])
```

Never send a message that contains only "Moving to the next issue" or
"Applying the fix now" — combine the confirmation and the next proposal
into one message.

---

## Step 6 — Save and summarise (one final cell)

After all issues are resolved, write ONE cell:

```python
from pathlib import Path
Path("data/output").mkdir(parents=True, exist_ok=True)
df_clean.to_parquet("data/output/cleaned.parquet", index=False)
print(f"Saved → data/output/cleaned.parquet")
print(f"Shape: {df_raw.shape} → {df_clean.shape}")
nulls = df_clean.isnull().sum()
print(f"Remaining nulls: {nulls[nulls>0].to_string() or 'None'}")
```

Then write ONE markdown summary cell covering all decisions made.

Tell the user: "Done. Type `tidy_notebook` when ready for the final check."
