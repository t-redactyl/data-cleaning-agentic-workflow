---
name: duplicate_detection
description: >
  Specialist skill for identifying and removing exact and near-duplicate rows.
  Called by clean_data. Always waits for user approval.
version: 1.0.0
---

# Skill: $duplicate_detection

## Step 1 — Profile

```python
n_exact = df_features.duplicated().sum()
print(f"Exact duplicate rows: {n_exact:,} ({n_exact/len(df_features)*100:.2f}%)")
if n_exact > 0:
    dupes = df_features[df_features.duplicated(keep=False)].sort_values(df_features.columns.tolist())
    print("\nSample duplicate rows:")
    print(dupes.head(10).to_string())
```

---

## Step 2 — Ask about the key

"I found [N] exact duplicate rows.

1. Is there a natural key — a column or set of columns that should uniquely
   identify each row? (e.g. `customer_id`, `order_id`, `user_id + date`)
   Type column names separated by commas, or 'all' for full-row matching.

2. Which row to keep when duplicates are found?
   a) First occurrence
   b) Last occurrence
   c) Most complete (fewest nulls)"

Wait for response.

---

## Step 3 — Check near-duplicates on key columns

If the user gave specific key columns:
```python
key_cols = [<user columns>]
near_dupes = df_features.duplicated(subset=key_cols, keep=False)
n_near = near_dupes.sum()
if n_near > n_exact:
    print(f"Near-duplicates on {key_cols}: {n_near:,} rows")
    print(df_features[near_dupes].sort_values(key_cols).head(20).to_string())
```

If near-duplicates exist: "Should I also deduplicate on just the key columns,
or only remove exact full-row duplicates?"

---

## Step 4 — Propose fix

### Keep most complete:
```
Fix: Remove duplicates, keeping the most complete row
Key: <cols> | Removed: <N> | Remaining: <N>

  def most_complete(group):
      return group.loc[group.isnull().sum(axis=1).idxmin()]

  df_clean = (
      df_clean
      .groupby(<key_cols>, as_index=False, sort=False)
      .apply(most_complete)
      .reset_index(drop=True)
  )
  print(f"Before: {len(df_features):,} | After: {len(df_clean):,} | Removed: {len(df_features)-len(df_clean):,}")
```

### Keep first/last:
```
Fix: Remove duplicates, keeping <first/last>
Key: <cols or 'all'> | Removed: <N> | Remaining: <N>

  df_clean = df_clean.drop_duplicates(
      subset=<key_cols or None>, keep="first"
  ).reset_index(drop=True)
  print(f"Before: {len(df_features):,} | After: {len(df_clean):,} | Removed: {len(df_features)-len(df_clean):,}")
```

---

## Step 5 — Wait for approval

"Apply this fix? (yes / no / modify: [instruction])"

---

## Step 6 — Write approved cells

**Markdown cell:**
```markdown
### Duplicate removal
- Exact duplicates: <N> rows (<X>%)
- Key columns: <cols>
- Strategy: Keep <first/last/most complete>
- Removed: <N> | Remaining: <N>
- Rationale: <one sentence>
```

**Code cell:**
```python
# --- Duplicates ---
print(f"Before: {len(df_clean):,} rows")
<approved code>
print(f"After:  {len(df_clean):,} rows | Removed: {len(df_features)-len(df_clean):,}")
```
