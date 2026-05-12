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

## On startup — three-stage check, in order

Do not ask any questions. Do not run any cells yet. Work through these
three checks in order and stop at the first one that succeeds.

### Check 1 — demo_issues.json (fastest path)

Use `mcp__pycharm__get_file_text_by_path` to read `data/demo_issues.json`.

If the file exists and is valid JSON:
- Load the issues list from it directly
- Note the dataset name, target column, and shape from the file
- Skip Check 2 and Check 3 entirely
- Go directly to **Step 2** — present the issue list and first fix

If the file does not exist, proceed to Check 2.

### Check 2 — runtime variables attachment

Read the `NotebookRuntimeVariablesRetrieverSource` attachment.

If `issues_df` is present in the runtime variables:
- Read the issues directly from the attachment
- Go directly to **Step 2**

If `issues_df` is absent but a source DataFrame is present (any DataFrame
not named `issues_df`, `missing_df`, `df_features`, or `df_clean`):
- Treat it as `df_raw` regardless of its actual variable name
- Proceed to Check 3

If NO DataFrame is present at all:
- Tell the user: "No source DataFrame found. Please run your data loading
  cell first, then type `clean_data` again."
- Stop.

### Check 3 — run the audit cell

No pre-computed issues are available. Run the audit cell in **Step 1**
once, then go to **Step 2**.

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

### Using distribution metadata

If the issue was loaded from `demo_issues.json` and has a `distribution`
object, use it as follows — do not ask questions that the metadata already
answers:

- Use `distribution.iqr_collapse_reason` to explain WHY the outlier was
  flagged, presented as context before the fix proposal
- Use `distribution.recommended_treatment` as the basis for the fix —
  do not override it with generic IQR/z-score logic
- Use `distribution.mechanism` and `distribution.mechanism_evidence` for
  missingness issues — do not run a correlation check
- Present the distribution stats (zeros_pct, median, IQR, etc.) as a
  brief context table before the fix proposal

If no `distribution` metadata is available, fall back to the standard
decision trees below.

---

### Outliers — with distribution metadata

Present in this format:

```
**Distribution of `<col>`:**
<render the key distribution fields as a small table>

**Why it was flagged:** <iqr_collapse_reason>

**Proposed fix:**
<recommended_treatment, translated into concrete code>
```

No questions — the metadata already contains the interpretation.

#### capital-gain (zero-inflated pattern)

```python
# Outliers: capital-gain (zero-inflated)
# Step 1: binary indicator for non-zero values
df_clean["capital_gain_nonzero"] = (df_clean["capital-gain"] > 0).astype(int)

# Step 2: log1p transform of non-zero values
df_clean["capital_gain_log1p"] = np.log1p(df_clean["capital-gain"])

# Step 3: flag top-coded sentinel values
df_clean["capital_gain_topcoded"] = (df_clean["capital-gain"] == 99999).astype(int)

print(f"Non-zero rows:    {df_clean['capital_gain_nonzero'].sum():,}")
print(f"Top-coded rows:   {df_clean['capital_gain_topcoded'].sum():,}")
print(f"Log1p range:      {df_clean['capital_gain_log1p'].min():.2f} – {df_clean['capital_gain_log1p'].max():.2f}")
```

#### hours-per-week (narrow distribution with tails)

```python
# Outliers: hours-per-week (narrow IQR, valid tails)
from scipy.stats.mstats import winsorize
df_clean["hours-per-week"] = winsorize(
    df_clean["hours-per-week"], limits=[0.01, 0.01]
).astype(float)
print(f"New range: [{df_clean['hours-per-week'].min():.0f}, {df_clean['hours-per-week'].max():.0f}] hours")
```

#### Outliers — without distribution metadata (fallback)

Ask ONE question only:
"Are the outliers in `<col>` data errors (a) or genuine extremes (b)?"

| Answer | Fix |
|--------|-----|
| a | Remove rows outside IQR 3× fence |
| b | skew > 1.0 → log1p transform; skew ≤ 1.0 → Winsorize 1/99th pct |

---

### Missingness — with distribution metadata

Present in this format:

```
**`<col>`:** <missing_count> missing (<missing_pct>%)
**Mechanism:** <mechanism> — <mechanism_evidence>
**Proposed fix:** <recommended_treatment, translated into code>
```

No mechanism diagnosis needed — read it directly from the metadata.

#### hours-per-week (MAR)

```python
# Missingness: hours-per-week (MAR — iterative imputation)
from sklearn.impute import IterativeImputer
from sklearn.linear_model import BayesianRidge

numeric_cols = df_clean.select_dtypes(include=np.number).columns.tolist()
imputer = IterativeImputer(estimator=BayesianRidge(), max_iter=10, random_state=42)
print(f"Before: {df_clean['hours-per-week'].isnull().sum()} missing")
df_clean[numeric_cols] = imputer.fit_transform(df_clean[numeric_cols])
print(f"After:  {df_clean['hours-per-week'].isnull().sum()} missing")
```

#### workclass (MNAR)

```python
# Missingness: workclass (MNAR — indicator + mode fill)
df_clean["workclass_was_missing"] = df_clean["workclass"].isnull().astype(int)
mode_val = df_clean["workclass"].mode()[0]
df_clean["workclass"] = df_clean["workclass"].fillna(mode_val)
print(f"Missing workclass filled with '{mode_val}'")
print(f"workclass_was_missing: {df_clean['workclass_was_missing'].sum():,} rows flagged")
```

#### Missingness — without distribution metadata (fallback)

| Condition | Fix |
|-----------|-----|
| < 1% | Fill: numeric → mean, categorical → mode |
| 1–30%, MCAR | KNN imputation (k=5) |
| 1–30%, MAR | Iterative imputation |
| Possible MNAR | Indicator column + median/mode fill |
| > 30% | Drop column |

---

### Duplicates

No question — propose immediately regardless of whether metadata is present:

```python
# Duplicates
print(f"Before: {len(df_clean):,} rows")
df_clean = df_clean.drop_duplicates(keep="first").reset_index(drop=True)
print(f"After:  {len(df_clean):,} rows")
```

---

### Markdown and code cell format (all issue types)

**Markdown cell:**
```markdown
### <Issue type>: `<col>`
- <key stats from distribution metadata or computed values>
- Mechanism/interpretation: <one sentence>
- Fix: <method>  |  Rationale: <one sentence>
```

**Code cell:** use the templates above, wrapped with before/after prints.

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
