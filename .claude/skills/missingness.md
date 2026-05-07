---
name: missingness
description: >
  Specialist skill for handling missing values. Called by the clean_data
  workflow. Diagnoses MCAR/MAR/MNAR, assesses severity, and recommends the
  statistically appropriate fix. Always waits for user approval.
version: 1.0.0
---

# Skill: $missingness

## Purpose
For a single column with missing values, diagnose WHY values are missing and
recommend the most appropriate treatment. Present reasoning, code, and the
affected row count — then wait for approval before writing anything.

---

## Step 1 — Quantify

```python
col = "<column_name>"
series = df_features[col]
n_total = len(series)
n_missing = series.isnull().sum()
pct_missing = n_missing / n_total * 100

print(f"Column:   {col}")
print(f"Dtype:    {series.dtype}")
print(f"Missing:  {n_missing:,} / {n_total:,}  ({pct_missing:.1f}%)")
print(f"\nSample non-null values:\n{series.dropna().head(10).to_string()}")
```

---

## Step 2 — Diagnose the mechanism

```python
# Check whether missingness correlates with other columns (MAR indicator)
miss_indicator = series.isnull().astype(int)
numeric_cols = df_features.select_dtypes(include=np.number).columns.tolist()
correlations = {}
for other_col in numeric_cols:
    if other_col == col:
        continue
    other_series = df_features[other_col].dropna()
    aligned = miss_indicator.loc[other_series.index]
    try:
        corr, p_val = stats.pointbiserialr(aligned, other_series)
        if p_val < 0.05 and abs(corr) > 0.1:
            correlations[other_col] = (round(corr, 3), round(p_val, 4))
    except Exception:
        pass

if correlations:
    print("Missingness correlates with (MAR evidence):")
    for c, (r, p) in correlations.items():
        print(f"  {c}: r={r}, p={p}")
else:
    print("No significant correlations — consistent with MCAR")
```

---

## Step 3 — Apply the decision tree

Choose ONE case and present it with full rationale.

### Case A — MCAR, < 1% missing
```
Proposed fix for `<col>`:
  Mechanism: MCAR | Severity: <1% — minimal impact
  Fix: Fill with mean (numeric) or mode (categorical)
  Rows affected: <N>

  fill_value = df_features["<col>"].mean()  # or .mode()[0]
  df_clean["<col>"] = df_features["<col>"].fillna(fill_value)
```

### Case B — MCAR, 1–30% missing
```
Proposed fix for `<col>`:
  Mechanism: MCAR | Severity: <X>% — mean imputation would bias variance
  Fix: KNN imputation (k=5) — preserves covariance structure

  from sklearn.impute import KNNImputer
  numeric_cols = df_features.select_dtypes(include=np.number).columns
  imputer = KNNImputer(n_neighbors=5)
  df_clean[numeric_cols] = imputer.fit_transform(df_features[numeric_cols])

Alternative: type 'modify: use iterative imputer'
```

### Case C — MAR (correlated with observed columns)
```
Proposed fix for `<col>`:
  Mechanism: MAR — correlated with: <list columns>
  Fix: Iterative (regression) imputation — statistically correct for MAR

  from sklearn.impute import IterativeImputer
  from sklearn.linear_model import BayesianRidge
  numeric_cols = [c for c in df_features.select_dtypes(include=np.number).columns
                  if c != TARGET_COL]
  imputer = IterativeImputer(estimator=BayesianRidge(), max_iter=10, random_state=42)
  df_imputed = df_features[numeric_cols].copy()
  df_imputed[:] = imputer.fit_transform(df_imputed)
  df_clean["<col>"] = df_imputed["<col>"]
```

### Case D — Possible MNAR
```
Proposed fix for `<col>`:
  Mechanism: Possible MNAR — missingness may encode information
  Fix: Create indicator column + median imputation

  df_clean["<col>_was_missing"] = df_features["<col>"].isnull().astype(int)
  df_clean["<col>"] = df_features["<col>"].fillna(df_features["<col>"].median())

Note: _was_missing lets the model learn from the missingness pattern.
Type 'modify: drop the column' if you prefer that instead.
```

### Case E — > 30% missing
```
Proposed fix for `<col>`:
  Severity: <X>% missing — imputation at this level risks substantial noise
  Fix: Drop the column
  Impact: 1 column removed

  df_clean = df_clean.drop(columns=["<col>"])

Type 'modify: keep and impute' to apply Case B treatment with a warning note.
```

---

## Step 4 — Wait for approval

"Apply this fix? (yes / no / modify: [instruction])"

Do NOT write any cells until receiving explicit approval.

---

## Step 5 — Write approved cells

**Markdown cell:**
```markdown
### Missingness: `<col>`
- Missing: <N> values (<X>%)
- Mechanism: <MCAR / MAR / MNAR>
- Method: <method name>
- Rationale: <one sentence>
- Affected: <N> rows/values
```

**Code cell:**
```python
# --- Missingness: <col> ---
print(f"Before: {df_features['<col>'].isnull().sum()} missing")
<approved code>
print(f"After:  {df_clean['<col>'].isnull().sum()} missing")
```
