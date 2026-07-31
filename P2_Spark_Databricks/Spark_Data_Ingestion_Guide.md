# Spark — How to Bring Data In

Topic: Data Ingestion into Spark  |  Saved: 2026-06-05

## 1. From Files (Most Common)
    
    
    # CSV
    df = spark.read.csv("path/to/file.csv", header=True, inferSchema=True)
    
    # JSON / JSONL
    df = spark.read.json("path/to/file.jsonl")
    
    # Parquet (columnar, compressed — preferred for production)
    df = spark.read.parquet("path/to/folder/")
    
    # Delta Lake (Databricks standard)
    df = spark.read.format("delta").load("path/to/delta-table/")

**Use when:** data is already on disk or cloud storage (S3, ADLS, GCS).

## 2. From a Database (JDBC)
    
    
    df = spark.read.format("jdbc") \
        .option("url", "jdbc:postgresql://host:5432/mydb") \
        .option("dbtable", "orders") \
        .option("user", "admin") \
        .option("password", "secret") \
        .load()

**Use when:** source is a relational database — PostgreSQL, MySQL, SQL Server, Oracle.

## 3. From a Python List (Small Data / Testing Only)
    
    
    data = [("BTC", 50000), ("ETH", 3000)]
    df = spark.createDataFrame(data, ["symbol", "price"])

**Use when:** quick tests or hardcoded small datasets. Not for production.

⚠️ Python 3.14 venv bug: `createDataFrame()` from a Python list throws a RecursionError. Workaround: write data to a file first and use `spark.read.json()` instead.

## 4. From a Catalog Table (Databricks / Hive)
    
    
    # If table is registered in Unity Catalog or Hive metastore
    df = spark.table("catalog.schema.orders")
    
    # Or via SQL
    df = spark.sql("SELECT * FROM orders WHERE status = 'active'")

**Use when:** working inside Databricks or a Hive-based environment where tables are already registered.

## 5. From a Streaming Source (Kafka / Kinesis)
    
    
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "localhost:9092") \
        .option("subscribe", "transactions") \
        .load()

**Use when:** processing real-time event streams — transactions, logs, IoT data. Returns a streaming DataFrame, not a static one.

## When to Use Which

Scenario| Method  
---|---  
Files on S3 / ADLS / GCS / local disk| `spark.read.csv/json/parquet()`  
Production relational database| JDBC  
Databricks registered table| `spark.table()`  
Quick test with small hardcoded data| `createDataFrame()`  
Real-time streaming (Kafka, Kinesis)| `spark.readStream`  
Best format for large-scale production| **Parquet or Delta** — columnar, compressed, fast  
  
**The Golden Rule:**  
Don't bring data to Spark that doesn't need to be there.  
If it fits in Pandas (< ~1GB, single machine) — use Pandas.  
Use Spark when data is too large for one machine, or you need distributed processing.  
  
The sweet spot: **files already on cloud storage (S3/ADLS) read as Parquet or Delta** — that's where Spark is genuinely faster than any alternative. 
