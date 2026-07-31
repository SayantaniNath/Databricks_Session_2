# Python DE Foundations — Topic 1: Generators & Iterators
# Exercises practiced: 2026-06-30

# ── Exercise 1 ── Basic generator ─────────────────────────────────────────────
# Write a generator that yields the square of every integer from 1 to n.
# Print the first 4 values using next().

def squares(n):
    i = 1
    while i <= n:
        yield i * i
        i += 1

g = squares(4)
print(next(g))  # 1
print(next(g))  # 4
print(next(g))  # 9
print(next(g))  # 16


# ── Exercise 2 ── Generator expression ────────────────────────────────────────
# Sum all even numbers in range(1_000_000) using a generator expression (one line).

numbers = range(1_000_000)
result = sum(i for i in numbers if i % 2 == 0)
print(result)  # 249999500000


# ── Exercise 3 ── Chunked file reader (DE core) ────────────────────────────────
# Generator that yields chunksize lines at a time from a file.
# Loop over it and print how many lines are in each chunk.

import itertools

def read_in_chunks(filepath, chunksize):
    with open(filepath) as f:
        while True:
            chunk = list(itertools.islice(f, chunksize))
            if not chunk:
                break
            yield chunk

# Usage (needs a real file):
# for c in read_in_chunks('myfile.txt', 10000):
#     print(len(c))


# ── Exercise 4 ── Spot the bug ─────────────────────────────────────────────────
# Bug: return exits after the first even number. Fix: replace return with yield.

def evens_up_to(n):
    for i in range(n):
        if i % 2 == 0:
            yield i          # was: return i

for val in evens_up_to(10):
    print(val)  # 0 2 4 6 8


# ══════════════════════════════════════════════════════════════════════════════
# Topic 2: Memory-Efficient Patterns
# Exercises practiced: 2026-06-30
# ══════════════════════════════════════════════════════════════════════════════

import pandas as pd

# ── Exercise 1 ── Chunked aggregation ─────────────────────────────────────────
# Read 10M-row sales.csv in chunks of 50,000. Compute total revenue per country
# across all chunks. Print top 3 countries by revenue.

results = []
for chunk in pd.read_csv('sales.csv', chunksize=50_000):
    results.append(chunk.groupby('country')['revenue'].sum())

top3 = pd.concat(results).groupby(level=0).sum().nlargest(3)
print(top3)

# Pattern: chunk → partial aggregate → collect → combine (same as MapReduce)
# level=0 = group by index (country became the index after groupby+sum on Series)
# Alternative: .sort_values(ascending=False).head(3)


# ── Exercise 2 ── dtype downcast ──────────────────────────────────────────────
# Downcast each column to the most memory-efficient dtype.
# customer_id: int, max 99999 → int32 (int16 only holds to 32,767)
# age: int, 0–120         → int8  (holds -128 to 127)
# country: string, 50 unique values → category
# score: float, 2 decimals → float32

df = pd.read_csv('customers.csv')
df['customer_id'] = df['customer_id'].astype('int32')
df['age']         = df['age'].astype('int8')
df['country']     = df['country'].astype('category')
df['score']       = df['score'].astype('float32')
print(df.memory_usage(deep=True).sum())

# category dtype: stores integer codes + one lookup table instead of repeating
# the full string per row — big savings for low-cardinality string columns.


# ── Exercise 3 ── Parquet read/write ──────────────────────────────────────────
# Read only 3 columns from a 200-column Parquet file (column pruning).
# Save a DataFrame back to Parquet with Snappy compression.

df = pd.read_parquet('transactions.parquet', columns=['user_id', 'amount', 'transaction_date'])
df.to_parquet('transactions.parquet', index=False, compression='snappy')

# Parquet reads only the needed columns off disk (columnar format).
# CSV would read all 200 columns and discard 197.
# In Spark, Parquet also enables predicate pushdown — filters hit storage
# before data reaches the executor.


# ── Key distinctions ───────────────────────────────────────────────────────────
# Iterable  — has __iter__()  — can be looped (list, str, file)
# Iterator  — has __next__() — stateful, one-directional
# Generator — iterator created with yield (or generator expression)
#
# DE relevance: pd.read_csv(filepath, chunksize=N) returns a generator of
# DataFrames — same lazy pattern as read_in_chunks above.


# ══════════════════════════════════════════════════════════════════════════════
# Topic 3: Pandas for DE
# Exercises practiced: 2026-06-30
# ══════════════════════════════════════════════════════════════════════════════

import numpy as np

# ── Exercise 1 ── groupby + named aggregations ────────────────────────────────
# Per region: total revenue, average units sold, number of products.

df.groupby('region').agg(
    total_revenue=('revenue', 'sum'),
    avg_units_sold=('units_sold', 'mean'),
    num_products=('product', 'count')
)

# Named agg syntax: result_col_name=('source_col', 'agg_function')
# Column names cannot have spaces — use underscores.


# ── Exercise 2 ── merge (LEFT JOIN) ───────────────────────────────────────────
# Keep all orders even if customer is missing. Result: order_id, amount, name, country.

result = orders.merge(customers, on='customer_id', how='left')[['order_id', 'amount', 'name', 'country']]

# how='left' keeps all rows from orders; name/country = NaN where no match.
# No .select() in pandas — that's PySpark. Column selection uses [[]] after merge.
# df['col']  → Series (1D)
# df[['col']] → DataFrame (2D) — use [[]] when selecting multiple columns.


# ── Exercise 3 ── apply vs vectorized ────────────────────────────────────────
# Part 1: replace apply with vectorized multiply
df['discount'] = df['revenue'] * 0.15           # was: .apply(lambda x: x * 0.15)

# Part 2: replace apply if/else with np.where
df['tier'] = np.where(df['revenue'] > 10_000, 'high', 'low')
# was: .apply(lambda x: 'high' if x > 10_000 else 'low')

# Rule:
# Math on a column          → df['col'] * value
# if/else on one column     → np.where(condition, true_val, false_val)
# Multiple conditions       → np.select([cond1, cond2], [val1, val2], default=...)
# Truly complex multi-col   → apply (last resort — Python loop, 10-100x slower)


# ══════════════════════════════════════════════════════════════════════════════
# Topic 4: Exception Handling
# Taught: 2026-06-30 | Exercises: TODO
# ══════════════════════════════════════════════════════════════════════════════

# try/except/finally
try:
    result = 10 / 0
except ZeroDivisionError:
    print("can't divide by zero")
finally:
    print("always runs — cleanup goes here")

# catch specific first, generic last
try:
    df = pd.read_csv('filepath.csv')
except FileNotFoundError:
    print("file not found")
except pd.errors.ParserError:
    print("CSV is malformed")
except Exception as e:
    print(f"unexpected error: {e}")

# custom exception — lets caller distinguish pipeline errors from library errors
class DataQualityError(Exception):
    pass

def validate(df):
    if df['revenue'].isnull().any():
        raise DataQualityError("revenue column has nulls")

# context manager — __exit__ closes resource even on crash
with open('file.csv') as f:
    data = f.read()

# DB connection pattern
# try:
#     conn = get_db_connection()
#     conn.execute(query)
# finally:
#     conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Topic 5: Functions Deep-Dive
# Taught: 2026-06-30 | Exercises: TODO — practice tomorrow
# ══════════════════════════════════════════════════════════════════════════════

# ── Exercise 1 ── *args and **kwargs ──────────────────────────────────────────
# Write a function `summarise(*args, **kwargs)` that:
# - prints the sum of all positional args
# - prints each keyword argument as "key: value"
# Call it with: summarise(1, 2, 3, name='Sayantani', role='DE')

def summarise(*args, **kwargs):
    print("Sum of positional args:", sum(args))
    for key, value in kwargs.items():
        print(f"{key}: {value}")



# ── Exercise 2 ── lambda + map + filter ───────────────────────────────────────
# You have: revenues = [500, 12000, 300, 8000, 15000]
# a) Use map to apply a 10% discount to every value (one line)
# b) Use filter to keep only values above 5000 (one line)
# c) Chain them: apply discount first, then keep values above 5000 (one line)

revenues = [500, 12000, 300, 8000, 15000]
list(map(lambda x: x * 0.9, revenues))  # a) [450.0, 10800.0, 270.0, 7200.0, 13500.0]
list(filter(lambda x: x > 5000, revenues))  # b) [12000, 8000, 15000]
list(filter(lambda x: x > 5000, map(lambda y: y * 0.9, revenues)))  # c) [10800.0, 7200.0, 13500.0]

# ── Exercise 3 ── decorator ───────────────────────────────────────────────────
# Write a decorator `timer` that prints how long a function takes to run.
# Apply it to a function `process(n)` that sums range(n).
# Use the `time` module: time.time() gives current timestamp in seconds.
# Call process(1_000_000) and see the output.




# ── Exercise 4 ── real DE use case ───────────────────────────────────────────
# Write a function `read_and_filter(filepath, **filters)` that:
# - reads a CSV into a DataFrame
# - for each key/value in filters, keeps only rows where df[key] == value
# - returns the filtered DataFrame
# Example call: read_and_filter('sales.csv', country='USA', product='Widget')

def read_and_filter(filepath, **filters):
    df = pd.read_csv(filepath)
    for key, value in filters.items():
        df = df[df[key] == value]
    return df
