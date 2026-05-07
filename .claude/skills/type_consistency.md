---
name: type_consistency
description: >
  Specialist skill for dtype mismatches, string noise in numeric columns,
  date columns stored as strings, and constant columns.
  Called by clean_data. Always waits for user approval.
version: 1.0.0
---

# Skill: $type_consistency

## Step 1 — Diagnose

### T1 — Numeric stored as object
```python
col = "<column_name>"
coerced = pd.to_numeric(df_features[col], errors="coerce")
failed = df_features[col][coerced.isnull() & df_features[col].notnull()]
print(f"Sample values:\n{df_features[col].head(20).to_string()}")
print(f"\nValues failing numeric coercion ({failed.nunique()} unique):")
print(failed.value_counts().head(20).to_string())
```

Common patterns: `$1,200`, `45%`, `" 42 "`, `N/A`, `NULL`, `-`

### T2 — Date stored as object
```python
col = "<column_name>"
coerced = pd.to_datetime(df_features[col], errors="coerce")
print(f"Sample: {df_features[col].head(5).to_string()}")
print(f"Parsed: {coerced.notnull().sum():,} | Failed: {coerced.isnull().sum():,}")
```

### T3 — Constant or near-constant
```python
print(df_features[col].value_counts().to_string())
```

---

## Step 2 — Propose fix

### T1:
```
Fix: Strip noise characters → coerce to numeric
Values coerced OK: <N> | Will become NaN: <N>

  df_clean["<col>"] = (
      df_features["<col>"]
      .astype(str).str.strip()
      .str.replace(r"[$,]", "", regex=True)   # adjust to actual noise
      .replace({"N/A": np.nan, "NULL": np.nan, "-": np.nan, "n/a": np.nan})
  )
  df_clean["<col>"] = pd.to_numeric(df_clean["<col>"], errors="coerce")
  print(f"Dtype: {df_clean['<col>'].dtype}")
  print(f"New nulls: {df_clean['<col>'].isnull().sum() - df_features['<col>'].isnull().sum()}")
```

### T2:
```
Fix: Parse to datetime64
Parsed OK: <N> | Will become NaT: <N>

  df_clean["<col>"] = pd.to_datetime(
      df_features["<col>"], errors="coerce", infer_datetime_format=True
  )
  print(f"Dtype: {df_clean['<col>'].dtype}")
  print(f"Range: {df_clean['<col>'].min()} → {df_clean['<col>'].max()}")

Type 'modify: extract date parts' to also add year/month/day columns.
```

### T3:
```
Fix: Drop constant column (no predictive information)
Impact: 1 column removed

  df_clean = df_clean.drop(columns=["<col>"])
  print(f"Dropped constant column '<col>'")

Type 'no' to keep it.
```

---

## Step 3 — Wait for approval

"Apply this fix? (yes / no / modify: [instruction])"

---

## Step 4 — Write approved cells

**Markdown cell:**
```markdown
### Type fix: `<col>`
- Issue: <describe problem>
- Before: `<old dtype>` | After: `<new dtype>`
- Values affected: <N> | Lost to NaN: <N>
- Rationale: <one sentence>
```

**Code cell:**
```python
# --- Type fix: <col> ---
print(f"Before: {df_features['<col>'].dtype}")
<approved code>
print(f"After:  {df_clean['<col>'].dtype}")
```
