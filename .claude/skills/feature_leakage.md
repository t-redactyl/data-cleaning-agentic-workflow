---
name: feature_leakage
description: >
  Specialist skill for detecting target leakage and ID columns.
  Called by clean_data. Always waits for user approval.
version: 1.0.0
---

# Skill: $feature_leakage

## Step 1 — Profile the flagged column

```python
col = "<column_name>"
series = df_features[col]
print(f"Column: {col} | Dtype: {series.dtype}")
print(f"Unique: {series.nunique():,} / {len(series):,}")
print(f"Sample:\n{series.head(10).to_string()}")

if TARGET_COL and series.dtype in [np.float64, np.int64]:
    corr = series.corr(df_raw[TARGET_COL])
    print(f"\nCorrelation with target `{TARGET_COL}`: {corr:.4f}")
```

---

## Step 2 — Present the issue and ask

### L1 — High correlation with target:

"Column `<col>` has a correlation of [X] with target `<TARGET_COL>`.

Is this column:
  a) Derived FROM the target (e.g. a subtotal when target is revenue) → leakage, must drop
  b) A legitimate feature known at prediction time → keep
  c) The target expressed differently → must drop

Please answer a, b, or c."

### L2 — ID column (cardinality = n_rows):

"Column `<col>` has one unique value per row — it appears to be an identifier.
ID columns cause overfitting and carry no generalisable signal.

Would you like to:
  a) Drop it entirely
  b) Keep it as a separate index Series outside df_clean (for traceability)"

---

## Step 3 — Propose fix

### L1a or L1c — Drop:
```
Fix: Drop `<col>` (target leakage)
  df_clean = df_clean.drop(columns=["<col>"])
  print(f"Dropped leaky column '<col>'")
```

### L1b — Keep with note:
```
Fix: Keep `<col>` (legitimate predictor — document in notebook)
  # '<col>' kept: legitimate predictor, known at prediction time
  # Correlation r=<X> is expected signal, not leakage
```

### L2a — Drop ID:
```
Fix: Drop ID column `<col>`
  df_clean = df_clean.drop(columns=["<col>"])
  print(f"Dropped ID column '<col>'")
```

### L2b — Preserve as index:
```
Fix: Save `<col>` separately, remove from features
  row_ids = df_clean["<col>"].copy()
  df_clean = df_clean.drop(columns=["<col>"])
  print(f"ID saved to row_ids ({len(row_ids):,} values)")
```

---

## Step 4 — Wait for approval

"Apply this fix? (yes / no / modify: [instruction])"

---

## Step 5 — Write approved cells

**Markdown cell:**
```markdown
### Leakage check: `<col>`
- Issue: <leakage / ID column>
- Evidence: <correlation value or cardinality>
- Decision: <drop / keep / preserve as index>
- Rationale: <one sentence>
```

**Code cell:**
```python
# --- Leakage: <col> ---
print(f"Columns before: {len(df_clean.columns)}")
<approved code>
print(f"Columns after:  {len(df_clean.columns)}")
```
