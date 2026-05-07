---
name: outlier_detection
description: >
  Specialist skill for identifying and treating outliers in numeric columns.
  Called by the clean_data workflow. Always waits for user approval.
version: 1.0.0
---

# Skill: $outlier_detection

## Step 1 — Profile

```python
col = "<column_name>"
series = df_features[col].dropna()

q1, q3 = series.quantile(0.25), series.quantile(0.75)
iqr = q3 - q1
lower_iqr = q1 - 3 * iqr
upper_iqr = q3 + 3 * iqr
mask_iqr = (series < lower_iqr) | (series > upper_iqr)
mask_z = np.abs(stats.zscore(series)) > 3

print(f"Column: {col}")
print(f"Range: [{series.min():.4g}, {series.max():.4g}]")
print(f"IQR fence (3×): [{lower_iqr:.4g}, {upper_iqr:.4g}]")
print(f"Outliers by IQR: {mask_iqr.sum():,}")
print(f"Outliers by z>3: {mask_z.sum():,}")
print(f"\nOutlier values (sample):\n{series[mask_iqr | mask_z].sort_values().head(20).to_string()}")
```

---

## Step 2 — Ask the domain question

"These [N] values in `<col>` fall outside the expected range
[show min/max outlier values].

Are these likely:
  a) Data entry or system errors (should be corrected/removed)
  b) Genuine extreme values that are real but rare
  c) Not sure (I'll suggest the most conservative approach)

Please reply a, b, or c."

Wait for response before proposing treatment.

---

## Step 3 — Propose treatment

### Answer A — Errors → remove rows
```
Fix: Remove rows where `<col>` is outside the IQR 3× fence
Rows removed: <N>

  outlier_mask = (
      (df_clean["<col>"] < {lower_iqr:.4g}) |
      (df_clean["<col>"] > {upper_iqr:.4g})
  )
  print(f"Removing {outlier_mask.sum()} rows")
  df_clean = df_clean[~outlier_mask].reset_index(drop=True)

Type 'modify: cap instead of remove' to Winsorize instead.
```

### Answer B — Genuine extremes

Check skewness first:
```python
skewness = series.skew()
print(f"Skewness: {skewness:.3f}")
```

If |skew| > 1.0 → log transform:
```
Fix: Log1p transform (right-skewed data — preserves order, compresses range)
New column: `<col>_log` (original kept for reference)

  df_clean["<col>_log"] = np.log1p(df_clean["<col>"])
  print(f"New skewness: {df_clean['<col>_log'].skew():.3f}")
```

If |skew| ≤ 1.0 → Winsorize:
```
Fix: Winsorize at 1st/99th percentile (caps extremes, preserves row count)

  from scipy.stats.mstats import winsorize
  df_clean["<col>"] = winsorize(df_clean["<col>"], limits=[0.01, 0.01])
  print(f"New range: [{df_clean['<col>'].min():.4g}, {df_clean['<col>'].max():.4g}]")
```

### Answer C — Not sure → flag only
```
Fix: Add binary outlier indicator column, keep all values

  outlier_mask = (
      (df_clean["<col>"] < {lower_iqr:.4g}) |
      (df_clean["<col>"] > {upper_iqr:.4g})
  )
  df_clean["<col>_is_outlier"] = outlier_mask.astype(int)
  print(f"Flagged {outlier_mask.sum()} rows in '<col>_is_outlier'")
```

---

## Step 4 — Wait for approval

"Apply this fix? (yes / no / modify: [instruction])"

---

## Step 5 — Write approved cells

**Markdown cell:**
```markdown
### Outlier treatment: `<col>`
- Outliers: <N> values (<X>%) outside IQR 3× fence
- Interpretation: <error / genuine extreme / uncertain>
- Method: <removal / log transform / Winsorize / flag>
- Rationale: <one sentence>
- Affected: <N> rows/values
```

**Code cell** with before/after stats:
```python
# --- Outliers: <col> ---
print(f"Before: min={df_features['<col>'].min():.4g}, max={df_features['<col>'].max():.4g}, n={len(df_features)}")
<approved code>
print(f"After:  min={df_clean['<col>'].min():.4g}, max={df_clean['<col>'].max():.4g}, n={len(df_clean)}")
```
