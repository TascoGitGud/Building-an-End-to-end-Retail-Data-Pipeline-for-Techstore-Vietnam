# 🏗️ Python / SQL / Power BI | Building an End-to-end Retail Data Pipeline for Techstore Vietnam

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Google BigQuery](https://img.shields.io/badge/Google_BigQuery-4285F4?style=flat-square&logo=googlebigquery&logoColor=white)
![Google Cloud Storage](https://img.shields.io/badge/Google_Cloud_Storage-4285F4?style=flat-square&logo=googlecloud&logoColor=white)
![Power BI](https://img.shields.io/badge/Tool-Power_BI-F2C811?style=flat-square&logo=powerbi&logoColor=black)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas&logoColor=white)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)

![Banner](Images/Banner.jpg)

_End-to-end Python ETL pipeline that ingests, cleans, and standardizes multi-channel retail sales and payment gateway data into a partitioned BigQuery Star Schema for unified business intelligence._

- 🎯 **Business Question:** How can we centralize fragmented sales channels and payment data into a single source of truth to track automated customer RFM segmentation, daily cash flows, and order payment health?
- 🏬 **Domain:** Technology Retail & E-commerce
- 🛠️ **Tools:** Python, Google Cloud Storage (GCS), Google BigQuery, Power BI

👤 Author: Bạch Minh Nam

---

## 📑 Table of Contents

1. [📌 Background & Overview](#-background--overview)
2. [🔌 Data Sources & Input](#-data-sources--input)
3. [🏛 Architecture & Design](#-architecture--design)
4. [⚒ ETL Pipeline Walkthrough](#-etl-pipeline-walkthrough)
5. [🌐 Data Warehouse Schema](#-data-warehouse-schema)
6. [🗄 Warehouse Output](#-warehouse-output)
7. [📈 Power BI Integration](#-power-bi-integration)
8. [🔎 Conclusion & Business Impact](#-conclusion--business-impact)
9. [🗂 Project Structure](#-project-structure)
10. [⚙ Setup Instructions](#-setup-instructions)

---

## 📌 Background & Overview

### Business Context

**TechStore Vietnam** is a technology retail company that sells across multiple channels - an online Shopify store, Sapo POS at physical locations, and other online order platforms. Customers pay through MoMo, ZaloPay, PayPal, and Mercury Bank.

Before this project, data from each channel lived in a separate system. There was no single place to see the full picture - how much was sold, whether payments were collected, or how customers behaved across channels.

### What This Project Does

This project builds a **Python ETL pipeline** that pulls data from all sources, cleans and standardises it, and loads it into a **Google BigQuery data warehouse** - so every team works from the same data.

✔️ Connects **8 data sources** (3 sales channels + 4 payment sources + cart tracking) into one place.

✔️ Organises data into a **Star Schema** with 4 active dimension tables and 5 fact tables, ready for analysis.

✔️ Runs **automatic data quality checks** at every step - catching nulls, duplicates, bad dates, and outliers before anything gets loaded.

✔️ After each run, automatically re-calculates **customer RFM segments** and lifetime value using a BigQuery SQL query.

✔️ Creates **3 ready-to-use views** for common business questions: customer journey, daily cashflow, and payment status.

### Who Is This Project For?

✔️ Data engineers looking at pipeline design patterns with GCP

✔️ Analytics engineers who want to see how multi-source ETL is structured in Python

✔️ Business teams who need a reliable, unified view of sales, payments, and customer behaviour

---

## 🔌 Data Sources & Input

All raw data is stored in **Google Cloud Storage (GCS)** as `.json.gz` files, one folder per source. The pipeline reads from GCS directly - no extra staging step needed.

| Source | Folder | Data Volume | Format |
|---|---|---|---|
| `Shopify` (Online Store) | `shopify/` | 2M customers · 200K orders · 1K products | `.json.gz` |
| `Sapo POS` (Offline Stores) | `sapo/` | 1M orders · 50 store locations | `.json.gz` |
| `Online Orders` (Multi-channel) | `online_orders/` | 50K orders | `.json.gz` |
| `PayPal` | `paypal/` | 300 transactions | `.json.gz` |
| `MoMo` | `momo/` | 500 transactions | `.json.gz` |
| `ZaloPay` | `zalopay/` | 500 transactions | `.json.gz` |
| `Mercury Bank` | `mercury/` | 3 accounts · 500 transactions | `.json.gz` |
| `Cart Tracking` | `cart_tracking/` | 10,000+ events | `.json.gz` |

### Raw Data Schemas

Each source has its own data format. Below are example:

**Shopify Orders**
```json
{
  "id": "int",
  "transaction_id": "string",
  "customer_id": "int",
  "order_date": "datetime",
  "payment_status": "string",
  "total_vnd": "int",
  "total_usd": "float",
  "line_items": "array",
  "source": "shopify"
}
```

> For full column details on all raw data, see the 📄 [Raw Data Dictionary](raw_data_dictionary.md)

---

## 🏛 Architecture & Design

### Pipeline Architecture

![Architecture](Images/Architecture.png)

*Figure 1: End-to-End Pipeline - GCS → ETL Engine → BigQuery → Power BI*

| Step | What Happens |
|---|---|
| **1. Extract** | The pipeline connects to GCS using a Storage service account and reads all `.json.gz` files. |
| **2. Transform** | Data is cleaned and reshaped in memory using Python and Pandas. |
| **3. Load** | Cleaned tables are written to BigQuery using a separate BigQuery service account. |
| **4. Visualise** | Power BI connects directly to BigQuery to display dashboards. |

---

## ⚒ ETL Pipeline Walkthrough

This pipeline follows a straightforward Extract, Transform, Load pattern, with two extra pieces added on top: a SQL step that recalculates customer segments right after loading finishes, and an orchestration layer that runs everything in order and keeps one broken data source from taking down the entire run.

### 1️⃣ Extract - Reading Files from GCS

Every table in this project starts as a `.json.gz` file sitting in a GCS bucket, one folder per source (`shopify/`, `sapo/`, `momo/`, `mercury/`, and so on). The job of this step is simple: connect to GCS, find the right files, unzip them, and load them into a Pandas DataFrame. Nothing gets cleaned or reshaped yet. Keeping this step this simple means that adding a new data source later only means writing one small class, nothing else in the pipeline has to change.

All extractors inherit from a single `Base_Extractor` class that handles the GCS connection, file listing, and unzipping logic. Each specific extractor only needs to know where its own files live.

<details>
<summary><b>📄 extractors/base_extractor.py</b>: Base_Extractor class</summary>

```python
class Base_Extractor:
    def __init__(self, bucket_name: str):
        self.logger = setup_logger(__name__)
        try:
            load_env_variables()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = get_gcs_credentials_path()
            self.client = storage.Client()
            self.bucket = self.client.bucket(bucket_name)
            self.logger.info('Successfully connected to GCS')
        except Exception as e:
            self.logger.error(f"Failed to connect to GCS: {e}")
            raise e

    def extract_json_gz(self, blob_path: str):
        try:
            blob = self.bucket.blob(blob_path)
            compressed_data = blob.download_as_bytes()
            decompressed_data = gzip.decompress(compressed_data)
            return json.loads(decompressed_data.decode("utf-8"))
        except Exception as e:
            self.logger.error(f"Failed to extract file {blob_path}: {e}")
            raise e

    def list_files(self, folder_name):
        try:
            blobs = self.client.list_blobs(self.bucket, prefix=folder_name)
            return [i.name for i in blobs if not i.name.endswith('/')]
        except Exception as e:
            self.logger.error(f"Error listing files in folder '{folder_name}': {e}")
            raise e
```

</details>

A specific extractor, like `Shopify_Extractor`, only adds its own folder path and a bit of logic to handle whether each file contains a list of records or a single record:

<details>
<summary><b>📄 extractors/shopify_extractor.py</b>: Shopify_Extractor class</summary>

```python
class Shopify_Extractor(Base_Extractor):
    def extract_file(self):
        files = self.list_files('shopify/')
        data_extract = []
        for i in files:
            data = self.extract_json_gz(i)
            if isinstance(data, list):
                data_extract.extend(data)
            elif isinstance(data, dict):
                data_extract.extend(data.get('id', [data]))
        return pd.DataFrame(data_extract)
```

</details>

`Sapo_Extractor`, `Online_Extractor`, and `Tracking_Extractor` are all built the exact same way. Only the folder path changes.

Payment data works a little differently. `Payment_Extractor` handles all four gateways from a single class, and Mercury Bank is the one source that comes back as two related tables instead of one, since bank data only really makes sense when accounts and transactions are looked at together:

<details>
<summary><b>📄 extractors/payment_extractor.py</b>: Payment_Extractor.payment_mercury_extract()</summary>

```python
def payment_mercury_extract(self):
    files = self.list_files('mercury/')
    data_extract = {}  # dict, because Mercury has 2 different data structures
    for i in files:
        data = self.extract_json_gz(i)
        df = pd.DataFrame(data)
        clean_key = i.split('/')[-1].replace('.json.gz', '')
        data_extract[clean_key] = df
    return data_extract  # {'accounts': df, 'transactions': df}
```

</details>

Once a file is extracted, the raw DataFrame goes straight into the matching transformer. There is no staging table in between.

---

### 2️⃣ Transform - Cleaning and Reshaping the Data

This is where most of the real work happens. Eight sources means eight different naming conventions, date formats, and quirks, and this step is what makes it possible for all of them to end up living safely in the same warehouse tables.

#### Shared logic in Base_Transformer

Both `Dim_Transformer` and `Fact_Transformer` inherit from `Base_Transformer`, which holds every reusable cleaning and key-generation utility used across the whole project:

| Method | Description |
|---|---|
| `to_date(df, columns)` | Converts text date columns into real datetime values. Invalid values become `NaT` instead of raising an error. |
| `convert_ns_to_us(df, date_formatted_column)` | Converts timestamp precision from nanoseconds to microseconds so BigQuery can accept the column. |
| `create_date_key(df, date_column, key_date)` | Creates an integer date key like `20240315` from a datetime column, used to link fact tables to the date dimension. |
| `create_surrogate_key(df, selected_cols, new_key_name)` | Builds a unique composite key by concatenating several columns together, e.g. `shopify_1042_TXN88`. |
| `create_order_key(df, source_col, order_id_col, new_key_name)` | Builds a unique order key by combining the source name with the order id. |
| `unflatten_list(df, list_col, col_to_keep)` | Explodes a column of nested lists, such as `line_items`, into separate rows. |
| `data_quality_check(df, table_name, ...)` | Counts nulls, flags duplicate rows with `is_deleted = 1`, validates that date columns fall in a sensible range, and finds outliers in amount columns using the IQR method. |
| `handle_missing_value(df, fill_cols)` | Fills specific null columns with safe default values, e.g. a guest `customer_id` becomes `-1`. |

Two representative examples of how these are written:

<details>
<summary><b>📄 transformers/base_transformer.py</b>: to_date()</summary>

```python
def to_date(self, df, columns: list):
    """Turns text columns into real dates. Bad values become NaT instead of throwing an error."""
    for i in columns:
        if i in df.columns:
            df[i] = pd.to_datetime(df[i], errors='coerce')
        else:
            self.logger.warning(f"Column '{i}' not found in DataFrame.")
    return df
```

</details>

<details>
<summary><b>📄 transformers/base_transformer.py</b>: create_surrogate_key()</summary>

```python
def create_surrogate_key(self, df, selected_cols: list, new_key_name="new_key_name"):
    """Builds a unique key by joining several columns together, e.g. 'shopify_1042_TXN88'."""
    missing_cols = [c for c in selected_cols if c not in df.columns]
    if missing_cols:
        self.logger.error(f"Columns {missing_cols} not found. Cannot create surrogate key.")
        return df

    combined_col = df[selected_cols[0]].astype(str)
    for c in selected_cols[1:]:
        combined_col = combined_col + "_" + df[c].astype(str)
    df[new_key_name] = combined_col
    return df
```

</details>

#### Dimension tables, built by Dim_Transformer

Dimension tables are fairly light, mostly renaming columns and fixing data types, since customer, product, and location data do not need to be reconciled across multiple sources:

- `dim_customer`, from Shopify. `customer_segment`, `first_order_date`, and `last_order_date` start out empty and get filled in later by the SQL step.
- `dim_product`, from Shopify. Adds an `is_active` flag.
- `dim_location`, from Sapo POS. Adds `location_type = 'Offline Store'`.

<details>
<summary><b>📄 transformers/dimension_transformer.py</b>: transform_dim_product()</summary>

```python
def transform_dim_product(self, df):  # from Shopify data
    col_mapping = {
        'id': 'product_id', 'name': 'product_name', 'sku': 'sku',
        'barcode': 'barcode', 'category': 'category', 'brand': 'brand',
        'price_vnd': 'price_vnd', 'price_usd': 'price_usd',
        'stock_quantity': 'stock_quantity'
    }
    selected_cols = [c for c in col_mapping.keys() if c in df.columns]
    df_dim = df[selected_cols].copy()
    df_dim.rename(columns=col_mapping, inplace=True)
    df_dim['is_active'] = 1
    return df_dim
```

</details>

#### Fact tables, built by Fact_Transformer

This is where things get more interesting:

- `fact_orders`, combining Shopify, Online Orders, and Sapo POS. Each channel is cleaned separately, then stacked together with `pd.concat`.
- `fact_order_items`, exploding the `line_items` array inside every order into individual product rows, then stacking all channels together.
- `fact_payments`, standardising ZaloPay, MoMo, and PayPal. Each gateway defines success differently, so all of them get mapped to the same `SUCCESS` / `FAILED` values. PayPal was left out of the final load because of very low data volume, but the transformer is kept for future use.
- `fact_cart_events`, mapping raw browsing behaviour (add to cart, view item, and so on) along with UTM tracking fields.
- `fact_bank_transactions`, processing Mercury Bank records. Negative amounts (money going out) are allowed here and clearly noted.

<details>
<summary><b>📄 transformers/fact_transformer.py</b>: transform_fact_order()</summary>

```python
def transform_fact_order(self, df_shopify, df_online, df_sapo):
    f_shopify = self.fact_order_shopify(df_shopify)
    f_online = self.fact_order_online(df_online)
    f_sapo = self.fact_order_sapo(df_sapo)

    fact_order = pd.concat([f_shopify, f_online, f_sapo], ignore_index=True)

    standard_cols = [
        'order_key', 'order_id', 'transaction_id', 'customer_id',
        'order_date', 'order_date_key', 'channel', 'source',
        'status', 'payment_status', 'total_vnd', 'total_usd'
    ]
    fact_order = fact_order[[c for c in standard_cols if c in fact_order.columns]]

    fact_order['total_vnd'] = fact_order['total_vnd'].fillna(0).astype('int64')
    fact_order['total_usd'] = fact_order['total_usd'].fillna(0.0).astype('float64')
    fact_order['order_date_key'] = fact_order['order_date_key'].fillna(19000101).astype('int32')
    return fact_order
```

</details>

And the payment gateway normalisation mentioned above, in code:

<details>
<summary><b>📄 transformers/fact_transformer.py</b>: payment status mapping (ZaloPay / MoMo)</summary>

```python
# ZaloPay marks success with return_code == 1
fact_payment_zalopay['payment_status'] = np.where(df['return_code'] == 1, 'SUCCESS', 'FAILED')

# MoMo uses resultCode == 0, a completely different convention
fact_payment_momo['payment_status'] = np.where(df['resultCode'] == 0, 'SUCCESS', 'FAILED')
```

</details>

Every transform function here gets called right after extraction and right before the quality check and the load. This step is really the bridge between raw JSON and a table people can actually trust.

---

### 3️⃣ Load - Writing to BigQuery

Once a table is clean, the goal here is simple: get it into BigQuery with the right schema, set up so queries against it run fast, not just correctly.

A single `Big_Query_Loader` class handles every table in the warehouse. Instead of hardcoding partitioning per table, it looks at the target column's data type and decides on its own whether to use time based partitioning (for real datetime columns) or range partitioning (for integer date keys like `20240315`):

<details>
<summary><b>📄 loaders/bigquery_loader.py</b>: load_dataframe(), auto partition detection</summary>

```python
def load_dataframe(self, df, dataset_id, bq_table_name,
                    write_disposition='WRITE_TRUNCATE',
                    partition_by=None, cluster_by=None):
    if df.empty:
        self.logger.warning(f"DataFrame for '{bq_table_name}' is empty. Skipping upload.")
        return

    destination_table = f"{self.client.project}.{dataset_id}.{bq_table_name}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=getattr(bigquery.WriteDisposition, write_disposition)
    )

    if partition_by:
        if partition_by in df.columns and pd.api.types.is_integer_dtype(df[partition_by]):
            job_config.range_partitioning = bigquery.RangePartitioning(
                field=partition_by,
                range_=bigquery.PartitionRange(start=19000101, end=21001231, interval=1)
            )
        else:
            job_config.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY, field=partition_by
            )

    if cluster_by:
        job_config.clustering_fields = cluster_by

    job = self.client.load_table_from_dataframe(df, destination_table, job_config=job_config)
    job.result()
```

</details>

And how the orchestrator actually calls it for `fact_orders`:

<details>
<summary><b>📄 orchestration/pipeline_orchestrator.py</b>: example load_dataframe() call</summary>

```python
self.loader.load_dataframe(
    df=fact_orders,
    dataset_id=self.dataset_id,
    bq_table_name='fact_orders',
    write_disposition='WRITE_TRUNCATE',
    partition_by='order_date_key',
    cluster_by=['customer_id', 'channel']
)
```

</details>

`fact_orders` is clustered on `customer_id` and `channel` because those are the two fields analysts filter on the most. Every table currently loads with `WRITE_TRUNCATE`, meaning a full reload on every run. This keeps things simple while data volume is still manageable, and it would be the first thing to move to an incremental load as the pipeline grows.

By the time a table reaches this step, it has already passed through cleaning and the quality check, so loading itself stays purely mechanical: take data that has already been validated and get it into BigQuery safely.

---

### 4️⃣ SQL Update - Customer RFM Segmentation

Marketing needs each customer classified into a segment based on how they actually spend, and that can only be calculated once `fact_orders` is fully loaded, since it depends on looking at order history across all three sales channels at once. This step closes that loop directly inside BigQuery, right after the load finishes, using a single `MERGE` statement run through `execute_query()`.

First, order history is aggregated per customer:

<details>
<summary><b>📄 orchestration/pipeline_orchestrator.py</b>: execute_sql_query(), aggregate_value CTE</summary>

```sql
WITH aggregate_value AS (
    SELECT
        customer_id,
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date,
        COUNT(DISTINCT order_key) AS total_orders,
        SUM(total_vnd) AS life_time_value_vnd
    FROM fact_orders
    WHERE payment_status IN ('paid', 'partially_paid')
      AND status IN ('completed', 'shipping', 'delivered', 'fulfilled', 'pending')
    GROUP BY customer_id
)
```

</details>

Then each customer gets a Recency, Frequency, and Monetary score from 1 to 5 using `NTILE(5)`, combined into a 3-digit RFM cell such as `555` or `312`:

<details>
<summary><b>📄 orchestration/pipeline_orchestrator.py</b>: execute_sql_query(), rfm_score CTE</summary>

```sql
rfm_score AS (
    SELECT
        customer_id,
        last_order_date AS recency,
        total_orders AS frequency,
        life_time_value_vnd AS monetary,
        NTILE(5) OVER (ORDER BY last_order_date)     AS r_score,
        NTILE(5) OVER (ORDER BY total_orders)        AS f_score,
        NTILE(5) OVER (ORDER BY life_time_value_vnd) AS m_score,
        CONCAT(
            CAST(NTILE(5) OVER (ORDER BY last_order_date)     AS STRING),
            CAST(NTILE(5) OVER (ORDER BY total_orders)        AS STRING),
            CAST(NTILE(5) OVER (ORDER BY life_time_value_vnd) AS STRING)
        ) AS rfm_cell
    FROM aggregate_value
)
```

</details>

That RFM cell is then mapped into one of six segments:

<details>
<summary><b>📄 orchestration/pipeline_orchestrator.py</b>: execute_sql_query(), rfm_segment CTE</summary>

```sql
rfm_segment AS (
    SELECT
        r.customer_id,
        a.first_order_date,
        a.last_order_date,
        a.total_orders,
        a.life_time_value_vnd,
        CASE
            WHEN rfm_cell IN ('555','554','544','545', ...) THEN 'VIP / Best Customers'
            WHEN rfm_cell IN ('553','551','552','541', ...) THEN 'Growing / Potential'
            WHEN rfm_cell IN ('535','534','443','434', ...) THEN 'Needs Attention'
            WHEN rfm_cell IN ('331','321','312','221', ...) THEN 'At Risk'
            WHEN rfm_cell IN ('155','154','144','214', ...) THEN 'Lost / Inactive'
            ELSE 'Unknown'
        END AS segment
    FROM rfm_score r
    LEFT JOIN aggregate_value a
        ON r.customer_id = a.customer_id
)
```

</details>

Notice this CTE joins back to `aggregate_value`, that's on purpose: `rfm_score` only carries `customer_id` and the RFM cell, so the actual dates and totals need to be pulled back in before the final merge. Each `rfm_cell` list above is shortened for readability, the real query spells out every 3-digit combination that falls into that segment.

Finally, everything is merged back into `dim_customer`. Customers with no purchase history at all are not dropped, a `LEFT JOIN` from `dim_customer` keeps them in the result and labels them `No Purchase`:

<details>
<summary><b>📄 orchestration/pipeline_orchestrator.py</b>: execute_sql_query(), final MERGE into dim_customer</summary>

```sql
MERGE dim_customer AS target
USING (
    SELECT
        d.customer_id,
        s.first_order_date,
        s.last_order_date,
        COALESCE(s.total_orders, 0) AS total_orders,
        s.life_time_value_vnd,
        COALESCE(s.segment, 'No Purchase') AS segment
    FROM dim_customer d
    LEFT JOIN rfm_segment s ON d.customer_id = s.customer_id
) AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN
UPDATE SET
    target.first_order_date    = source.first_order_date,
    target.last_order_date     = source.last_order_date,
    target.total_orders        = source.total_orders,
    target.life_time_value_vnd = source.life_time_value_vnd,
    target.customer_segment    = source.segment;
```

</details>

This step only runs once `process_facts()` finishes, since it is the one part of the pipeline that depends on `fact_orders` already being loaded. Everything before it is pure ETL. This is the one place where raw transactions turn into something Marketing can actually act on.

---

### 5️⃣ Orchestration and Error Handling

The final piece ties every extractor, transformer, and loader together into one run, and makes sure that if one of the eight sources has a bad day, the other seven still make it into the warehouse.

`Pipeline_Orchestrator` exposes a single entry point, `orchestrator_run()`, that runs everything in order:

<details>
<summary><b>📄 orchestration/pipeline_orchestrator.py</b>: orchestrator_run(), the single entry point</summary>

```python
def orchestrator_run(self):
    self.logger.info(">>> PIPELINE STARTED <<<")
    try:
        self.loader.check_dataset_available(self.dataset_id)
        self.process_dimensions()   # dim_customer, dim_product, dim_location
        self.process_facts()        # fact_orders, fact_order_items, fact_payments, ...
        self.execute_sql_query()    # RFM segmentation MERGE
        self.logger.info(">>> PIPELINE FINISHED SUCCESSFULLY <<<")
    except Exception as e:
        self.logger.critical(f">>> PIPELINE FAILED: {e} <<<")
        raise e
```

</details>

What matters even more than this outer wrapper is that error handling is also applied at the table level, inside `process_dimensions()` and `process_facts()`. A broken file in `cart_tracking/` should never be able to stop `dim_customer` from loading:

<details>
<summary><b>📄 orchestration/pipeline_orchestrator.py</b>: process_dimensions(), isolated try/except per table</summary>

```python
try:
    self.logger.info("Processing 'dim_customer'...")
    extractor = Shopify_Extractor(self.bucket_name)
    customer_data_raw = extractor.extract_file()

    dim_customer = self.dim_transformer.transform_dim_customer(customer_data_raw)
    self.dim_transformer.data_quality_check(df=dim_customer, table_name='dim_customer')

    self.loader.load_dataframe(
        df=dim_customer, dataset_id=self.dataset_id,
        partition_by='created_at', bq_table_name='dim_customer'
    )
    self.logger.info("Finished 'dim_customer'.")

except Exception as e:
    self.logger.critical(f'Fail when processing DIM_CUSTOMER: {e}')
    raise e  # logged clearly, but does not stop the next table's own try/except
```

</details>

`dim_product` and `dim_location` follow this exact same pattern, each wrapped in its own try/except block. Every step, whether it succeeds or fails, gets logged to both the console and a log file through a shared `setup_logger()` utility, so there is always a clear record of what happened during a run.

This is really the layer that turns four separate modules into an actual working product. One command, `python main.py`, runs the entire eight source pipeline from start to finish, reports on its own health along the way, and keeps working even when one part of it does not.

---

## 🌐 Data Warehouse Schema

![Star Schema Data Model](Images/Star_Schema_Data_Model.png)

*Figure 2: Star Schema*

Dimension tables describe the "who", "what", "where", and "when". Fact tables record what actually happened (orders, payments, events) and link back to dimensions via foreign keys.

### 🧩 Dimension Tables

| Table | Source | Partition | Primary Key | What It Records |
|---|---|---|---|---|
| `dim_customer` | `Shopify` | `created_at` | `customer_id` | Customer profile + RFM segment, lifetime value, etc.. Updated automatically after each pipeline run. |
| `dim_product` | `Shopify` | - | `product_id` | Product name, SKU, category, etc. |
| `dim_location` | `Sapo POS` | - | `location_id` | Store name, code, city, address, phone. `location_type` = `Offline Store`. |
| `dim_date` | - | - | `date_key` | Date attributes: year, quarter, month, etc. |

> `dim_staff` was part of the original scope but **not built** - Sapo POS raw data does not include staff information.

### 🧾 Fact Tables

| Table | Sources | Partition | Primary Key | What It Records |
|---|---|---|---|---|
| `fact_orders` | `Shopify` · `Online Orders` · `Sapo POS` | `order_date_key` | `order_key` | Every order across all channels. |
| `fact_order_items` | `Shopify` · `Online Orders` · `Sapo POS` | `order_date_key`  | `order_item_key` | Each product line inside an order. |
| `fact_payments` | `ZaloPay` · `MoMo` · `PayPal` | `payment_date_key` | `payment_key` | Payment transactions from e-wallet gateways. |
| `fact_cart_events` | `Cart Tracking` | `event_date_key` | `event_key` | User actions on site. |
| `fact_bank_transactions` | `Mercury Bank` | `transaction_date_key` | `transaction_key` | Bank-level inflows and outflows. |

### 🔍 Analytical Views

Three views sit on top of the fact tables and are ready to query directly from Power BI:

| View | Built From | What It Answers |
|---|---|---|
| `vw_customer_journey` | `fact_cart_events` + `fact_orders` | How did each customer move from first interaction to purchase? |
| `vw_cashflow_daily` | `fact_orders` + `fact_payments` + `fact_bank_transactions` + `dim_date` | What came in and went out each day? |
| `vw_payment_status` | `fact_orders` + `fact_payments` | Is each order actually paid? |

> For full column details on all tables, see the 📄 [Data Dictionary](data_dictionary.md)

---

## 🗄 Warehouse Output

The screenshots below show real query results from BigQuery after the pipeline has run.

### `dim_customer` - RFM Segments Auto-Updated

![dim_customer](Images/Dim_customer.png)

`dim_customer` is updated after every pipeline run via the BigQuery MERGE. The table shows each customer's recalculated `lifetime_value_vnd`, `total_orders`, `last_order_date`, and their current RFM segment, including `No Purchase` for customers with no order history (`total_orders = 0` and `first_order_date` / `last_order_date` left as `null`).

> The full `MERGE` statement behind this table is shown in [Main Process, Step 4️⃣ SQL Update](#4️⃣-sql-update---customer-rfm-segmentation).

### `vw_cashflow_daily` - Daily Revenue and Cashflow

![vw_cashflow_daily](Images/vw_cashflow_daily.png)

`vw_cashflow_daily` brings together sales, payments, and bank records into one row per day. Finance can check whether revenue was actually collected without joining tables manually.

<details>
<summary><b>📄 BigQuery View</b>: vw_cashflow_daily</summary>

```sql
CREATE OR REPLACE VIEW `unigappython.techstore_analytics.vw_cashflow_daily` AS
WITH sales AS (
  SELECT
    order_date_key AS date_key,
    SUM(total_vnd) AS sales_revenue_vnd,
    COUNT(DISTINCT order_key) AS total_orders
  FROM `unigappython.techstore_analytics.fact_orders`
  WHERE status NOT IN ('cancelled', 'refunded')
  GROUP BY order_date_key
),

payments AS (
  SELECT
    payment_date_key AS date_key,
    SUM(IF(payment_status = 'success', amount_vnd, 0)) AS payment_received_vnd,
    SUM(IF(payment_status = 'refunded', amount_vnd, 0)) AS payment_refunded_vnd,
    COUNT(DISTINCT transaction_id) AS total_payment_transactions
  FROM `unigappython.techstore_analytics.fact_payments`
  GROUP BY payment_date_key
),

bank AS (
  SELECT
    transaction_date_key AS date_key,
    SUM(IF(transaction_type = 'inflow' AND status = 'completed', amount_vnd, 0)) AS bank_inflow_vnd,
    SUM(IF(transaction_type = 'outflow' AND status = 'completed', amount_vnd, 0)) AS bank_outflow_vnd
  FROM `unigappython.techstore_analytics.fact_bank_transactions`
  GROUP BY transaction_date_key
),

all_dates AS (
  SELECT date_key FROM sales
  UNION DISTINCT
  SELECT date_key FROM payments
  UNION DISTINCT
  SELECT date_key FROM bank
)

SELECT
  d.date_key,
  dd.year,
  dd.month,
  dd.month_name,
  dd.day_name,
  dd.is_weekend,
  IFNULL(s.sales_revenue_vnd, 0) AS sales_revenue_vnd,
  IFNULL(s.total_orders, 0) AS total_orders,
  IFNULL(p.payment_received_vnd, 0) AS payment_received_vnd,
  IFNULL(p.payment_refunded_vnd, 0) AS payment_refunded_vnd,
  IFNULL(p.total_payment_transactions, 0) AS total_payment_transactions,
  IFNULL(b.bank_inflow_vnd, 0) AS bank_inflow_vnd,
  IFNULL(b.bank_outflow_vnd, 0) AS bank_outflow_vnd,
  (IFNULL(b.bank_inflow_vnd, 0) - IFNULL(b.bank_outflow_vnd, 0)) AS net_bank_cashflow_vnd,
  (IFNULL(p.payment_received_vnd, 0) - IFNULL(p.payment_refunded_vnd, 0)
    + IFNULL(b.bank_inflow_vnd, 0) - IFNULL(b.bank_outflow_vnd, 0)) AS net_cashflow_vnd
FROM all_dates d
LEFT JOIN sales s ON d.date_key = s.date_key
LEFT JOIN payments p ON d.date_key = p.date_key
LEFT JOIN bank b ON d.date_key = b.date_key
LEFT JOIN `unigappython.techstore_analytics.dim_date` dd ON d.date_key = dd.date_key
ORDER BY d.date_key;
```

The view unions three independent aggregates (`sales`, `payments`, `bank`), one row per `date_key`, then left-joins them all together so a day with sales but no bank activity yet still shows up with zeros instead of disappearing from the report.

</details>

### `vw_customer_journey` - Touchpoint Sequence Per Customer

![vw_customer_journey](Images/vw_customer_journey.png)

`vw_customer_journey` shows each customer's path from first site interaction to purchase, including the full event sequence (e.g. `view_item > add_to_cart > purchase`) and how many hours it took.

<details>
<summary><b>📄 BigQuery View</b>: vw_customer_journey</summary>

```sql
CREATE OR REPLACE VIEW `unigappython.techstore_analytics.vw_customer_journey` AS
WITH events_unioned AS (
  SELECT
    customer_id,
    session_id,
    event_type,
    event_timestamp,
    product_id,
    source,
    device,
    utm_source,
    utm_campaign,
    NULL AS order_id,
    NULL AS order_total_vnd
  FROM `unigappython.techstore_analytics.fact_cart_events`
  WHERE customer_id IS NOT NULL
    AND customer_id != -1

  UNION ALL

  SELECT
    customer_id,
    NULL AS session_id,
    'purchase' AS event_type,
    order_date AS event_timestamp,
    NULL AS product_id,
    source,
    NULL AS device,
    NULL AS utm_source,
    NULL AS utm_campaign,
    order_id,
    total_vnd AS order_total_vnd
  FROM `unigappython.techstore_analytics.fact_orders`
  WHERE customer_id IS NOT NULL
    AND customer_id != -1
    AND order_date IS NOT NULL
),

ranked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY event_timestamp ASC
    ) AS touchpoint_seq,
    MIN(event_timestamp) OVER (PARTITION BY customer_id) AS first_touchpoint_at,
    MAX(IF(event_type = 'purchase', event_timestamp, NULL))
      OVER (PARTITION BY customer_id) AS first_purchase_at
  FROM events_unioned
)

SELECT
  customer_id,
  touchpoint_seq,
  event_type,
  event_timestamp,
  session_id,
  product_id,
  source,
  device,
  utm_source,
  utm_campaign,
  order_id,
  order_total_vnd,
  first_touchpoint_at,
  first_purchase_at,
  TIMESTAMP_DIFF(first_purchase_at, first_touchpoint_at, HOUR) AS hours_to_first_purchase,
  STRING_AGG(event_type, ' > ')
    OVER (
      PARTITION BY customer_id
      ORDER BY event_timestamp ASC
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS touchpoint_sequence
FROM ranked
ORDER BY customer_id, touchpoint_seq;
```

Browsing events from `fact_cart_events` and purchases from `fact_orders` are unioned into a single timeline per customer, then `STRING_AGG` builds a running, human-readable sequence like `view_item > add_to_cart > purchase` for every touchpoint along the way.

</details>

### `vw_payment_status` - Payment Health Per Order

![vw_payment_status](Images/vw_payment_status.png)

`vw_payment_status` joins orders and payments to classify every order's payment health and flag overdue or partially paid orders.

<details>
<summary><b>📄 BigQuery View</b>: vw_payment_status</summary>

```sql
CREATE OR REPLACE VIEW `unigappython.techstore_analytics.vw_payment_status` AS
WITH payment_agg AS (
  SELECT
    order_id,
    SUM(IF(payment_status = 'success', amount_vnd, 0)) AS total_paid_vnd,
    MIN(IF(payment_status = 'success', payment_date, NULL)) AS first_success_payment_date,
    MAX(payment_date) AS last_payment_date,
    ARRAY_AGG(payment_gateway ORDER BY payment_date DESC LIMIT 1)[OFFSET(0)] AS last_payment_gateway,
    ARRAY_AGG(payment_method ORDER BY payment_date DESC LIMIT 1)[OFFSET(0)] AS last_payment_method
  FROM `unigappython.techstore_analytics.fact_payments`
  GROUP BY order_id
)

SELECT
  o.order_key,
  o.order_id,
  o.transaction_id,
  o.customer_id,
  o.order_date,
  o.channel,
  o.status AS order_status,
  o.payment_status AS order_payment_status,
  o.total_vnd AS order_total_vnd,
  IFNULL(p.total_paid_vnd, 0) AS total_paid_vnd,
  (o.total_vnd - IFNULL(p.total_paid_vnd, 0)) AS outstanding_amount_vnd,
  p.first_success_payment_date,
  p.last_payment_date,
  p.last_payment_gateway,
  p.last_payment_method,
  TIMESTAMP_DIFF(p.first_success_payment_date, o.order_date, HOUR) AS payment_delay_hours,

  CASE
    WHEN IFNULL(p.total_paid_vnd, 0) >= o.total_vnd
      THEN 'Paid'
    WHEN IFNULL(p.total_paid_vnd, 0) = 0
         AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), o.order_date, HOUR) <= 24
      THEN 'Pending'
    WHEN IFNULL(p.total_paid_vnd, 0) = 0
         AND TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), o.order_date, HOUR) > 24
      THEN 'Overdue'
    WHEN IFNULL(p.total_paid_vnd, 0) > 0
         AND IFNULL(p.total_paid_vnd, 0) < o.total_vnd
      THEN 'Partially Paid'
    WHEN o.status = 'cancelled'
      THEN 'Cancelled'
    ELSE 'Unknown'
  END AS payment_status_category

FROM `unigappython.techstore_analytics.fact_orders` o
LEFT JOIN payment_agg p
  ON o.order_id = p.order_id
ORDER BY o.order_date DESC;
```

Every order is classified into one of six payment health categories (`Paid`, `Pending`, `Overdue`, `Partially Paid`, `Cancelled`, `Unknown`) based on how much has been paid so far and how much time has passed since the order was placed, so Finance can filter straight to the orders that need attention.

</details>

---

## 📈 Power BI Integration

The three analytical views (`vw_customer_journey`, `vw_cashflow_daily`, `vw_payment_status`) are connected to Power BI via the native BigQuery connector for future business reporting.

### Data Model View in Power BI

![Power BI Model View](Images/PBImodelview.png)

*Figure 3: The three views loaded into Power BI's model view.*

---

## 🔎 Conclusion & Business Impact

📍 **Key Outcomes:**

✔️ **One place for all data** - sales from Shopify, Sapo POS, and online channels; payments from MoMo, ZaloPay, PayPal, and Mercury; and user behaviour from cart tracking - all cleaned and in one BigQuery dataset.

✔️ **Faster reporting** - the analytics team gets clean, structured tables they can query directly. No more manual exports or fixing mismatched formats before each report.

✔️ **Daily cashflow visibility** - Finance can check whether money was actually received each day with a single query against `vw_cashflow_daily`.

✔️ **Always up-to-date customer segments** - Marketing gets fresh RFM segments automatically after every pipeline run, without a separate tool or manual step.

✔️ **Easy to extend** - adding a new data source only means writing a new extractor class. Everything else (cleaning logic, loader, orchestrator) stays the same.

---

## 🗂 Project Structure

```
ETL Pipeline/
├── config/
│   └── config.txt                    # Configuration template
├── 
│   ├── data_dictionary.md            # Full column-level documentation
│   └── Images/                       # Architecture diagrams and screenshots
├── extractors/
│   ├── __init__.py
│   ├── base_extractor.py             # Shared GCS logic: connect, list files, unzip
│   ├── online_extractor.py           # Online orders (multi-channel)
│   ├── payment_extractor.py          # Mercury, MoMo, PayPal, ZaloPay
│   ├── sapo_extractor.py             # Sapo POS offline orders
│   ├── shopify_extractor.py          # Shopify online store
│   └── tracking_extractor.py         # Cart tracking events
├── loaders/
│   ├── __init__.py
│   └── bigquery_loader.py            # Writes to BigQuery with partitioning and clustering
├── orchestration/
│   ├── __init__.py
│   └── pipeline_orchestrator.py      # Runs the full pipeline in order
├── transformers/
│   ├── __init__.py
│   ├── base_transformer.py           # Shared cleaning, key generation, quality checks
│   ├── dimension_transformer.py      # Builds dim_customer, dim_product, dim_location
│   └── fact_transformer.py           # Builds all five fact tables
├── utils/
│   ├── __init__.py
│   ├── config.py                     # Loads environment variables and credential paths
│   └── logger.py                     # Logs to both console and file
├── tests/
│   ├── check_data.py
│   ├── test_extract.py
│   ├── test_load.py
│   └── test_transform.py
├── logs/                             # Pipeline run logs (auto-created)
├── .env.example                      # Example environment config
├── main.py                           # Entry point - run this to start the pipeline
└── requirement.txt                   # Python dependencies
```

---

## ⚙ Setup Instructions

### What You Need

- Python 3.8 or higher
- A Google Cloud account with BigQuery and Cloud Storage enabled
- A service account with **BigQuery Admin** and **Storage Object Viewer** permissions

### Steps

**1. Clone the repo**
```bash
https://github.com/TascoGitGud/Building-an-End-to-end-Retail-Data-Pipeline-for-Techstore-Vietnam.git
```
**2. Install dependencies**
```bash
pip install -r requirement.txt
```

**3. Set up credentials**

Fill in your GCP credential file paths:

```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/gcs_service_account.json
GOOGLE_APPLICATION_CREDENTIALS_BIGQUERY=path/to/bigquery_service_account.json
```

> GCP credentials are not included in this repo for security reasons.

**4. Set your bucket and dataset**

In `main.py`, update these two lines:
```python
BUCKET_NAME = 'your-gcs-bucket-name'
DATASET_ID = 'your-dataset'
```

**5. Run the pipeline**
```bash
python main.py
```

The pipeline will log every step to the console and to `logs/pipeline.log`. When it finishes, all tables and views will be available in BigQuery under the dataset you configured.


---

