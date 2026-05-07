---
name: explore_db
description: >
  Workflow 1. Helps the user understand the Postgres database structure and
  drafts a SQL query to load the dataset of interest. The user runs the query
  themselves in a SQL cell. Claude does not load data directly.
version: 1.0.0
trigger: "explore_db"
---

# Workflow 1: `explore_db`

## Purpose
You want to understand what tables exist in the database, what their schemas
look like, and what query will give you the dataset you want to clean.
Claude helps you work this out. You write the final query into a SQL cell
yourself and inspect the result in the DataFrame viewer.

---

## Step 1 — Discover the database structure

Use the Postgres MCP tool to list all available tables. Present them clearly:

```
Tables available in the connected database:
  1. table_name_1
  2. table_name_2
  ...

Which table (or tables) are you interested in?
```

Wait for the user's response.

---

## Step 2 — Inspect the schema of the chosen table(s)

For each table the user names, use the MCP tool to retrieve:
- Column names and data types
- Primary key(s) and foreign keys if available
- Approximate row count (`SELECT COUNT(*) FROM table`)
- A small sample (`SELECT * FROM table LIMIT 5`)

Present this as a readable summary:

```
Table: <table_name>
Rows (approx): X,XXX

Columns:
  id            integer       PRIMARY KEY
  customer_name varchar(255)
  created_at    timestamp
  ...

Sample rows:
  [formatted table of 5 rows]
```

---

## Step 3 — Ask what the user wants to achieve

Ask:
"What are you trying to do with this data?
For example:
  - Load a single table as-is
  - Join two tables together
  - Filter to a specific subset (date range, category, etc.)
  - Aggregate before loading

What does your analysis need?"

Wait for the response.

---

## Step 4 — Draft the SQL query

Based on the schema and the user's goal, draft a SQL query. Explain the
choices made (which columns, any filters, any joins, any ordering).

Present the query clearly:

```sql
-- Suggested query for <purpose>
SELECT
    t1.id,
    t1.customer_name,
    t1.created_at,
    t2.product_name,
    t2.amount
FROM orders t1
JOIN order_items t2 ON t1.id = t2.order_id
WHERE t1.created_at >= '2023-01-01'
ORDER BY t1.created_at DESC;
```

Then explain:
- Why each column was included or excluded
- What the WHERE clause does
- Whether a LIMIT is appropriate for initial inspection (recommend LIMIT 10000
  for first load, remove once happy with the query)

---

## Step 5 — Provide the Jupyter SQL cell to paste

Give the user the exact cell content to paste into their notebook, using
PyCharm's SQL cell magic:

```python
# Cell type: SQL (use PyCharm's %% sql cell, or ipython-sql magic)

%%sql df_raw <<
SELECT
    t1.id,
    ...
FROM ...
LIMIT 10000
```

Then tell the user:

"Paste this into a SQL cell in your notebook and run it. This loads the result
directly into `df_raw` as a pandas DataFrame.

Once you've inspected the data in the DataFrame viewer and are happy with the
query, remove the LIMIT and re-run to load the full dataset.

When you're ready to start cleaning, type `clean_data`."

---

## Step 6 — Answer follow-up questions

Remain available for follow-up questions such as:
- "Can you add a filter for X?"
- "What does column Y mean?"
- "Are there any NULLs in column Z?"  ← use MCP to check
- "How many rows match this condition?" ← use MCP to run a COUNT query

For any exploratory question that can be answered with a quick MCP query
(COUNT, DISTINCT values, NULL check), run it and show the result rather than
asking the user to write the query themselves.
