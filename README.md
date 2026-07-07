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
2. [📂 Data Sources](#-data-sources)
3. [🏛 Architecture & Design](#-architecture--design)
4. [⚒ Main Process](#-main-process)
5. [🗄 Data Model (Star Schema)](#-data-model-star-schema)
6. [📊 BigQuery Output](#-bigquery-output)
7. [📈 Power BI](#-power-bi)
8. [🗂 Project Structure](#-project-structure)
9. [🔎 Conclusion & Business Impact](#-conclusion--business-impact)
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

## 📂 Data Sources

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

## ⚒ Main Process

### Step 1: Extract - Reading files from GCS

Each data source has its own extractor class that knows where its files live. All extractors share the same base logic (connect to GCS, list files, unzip and read `.json.gz`) through a `Base_Extractor` class - so there's no repeated code across 5 different sources.

<details>
<summary><b>📄 View code — <code>Base_Extractor.extract_json_gz()</code> / <code>list_files()</code></b></summary>

```python
def extract_json_gz(self, blob_path: str):
    blob = self.bucket.blob(blob_path)
    compressed_data = blob.download_as_bytes()
    decompressed_data = gzip.decompress(compressed_data)
    return json.loads(decompressed_data.decode("utf-8"))

def list_files(self, folder_name):
    blobs = self.client.list_blobs(self.bucket, prefix=folder_name)
    return [i.name for i in blobs if not i.name.endswith('/')]
```

</details>

<details>
<summary><b>📄 View code — <code>Shopify_Extractor.extract_file()</code> (inherits from Base_Extractor)</b></summary>

```python
class Shopify_Extractor(Base_Extractor):
    def extract_file(self):
        list_files_extract = self.list_files('shopify/')
        data_extract = []
        for i in list_files_extract:
            data = self.extract_json_gz(i)
            data_extract.extend(data if isinstance(data, list) else [data])
        return pd.DataFrame(data_extract)
```

</details>

`Payment_Extractor` handles all four payment gateways in one class. Mercury Bank is a special case - it returns two separate tables (`accounts` and `transactions`), while ZaloPay, MoMo, and PayPal each return a single flat table.

<details>
<summary><b>📄 View code — <code>Payment_Extractor.payment_mercury_extract()</code></b></summary>

```python
def payment_mercury_extract(self):
    "Create extract function for payment gateway: mercury"
    list_files_extract = self.list_files('mercury/')

    data_extract = {}  # Dict because Mercury returns 2 different data structures
    for i in list_files_extract:
        data = self.extract_json_gz(i)
        df = pd.DataFrame(data)
        clean_key = i.split('/')[-1].replace('.json.gz', '')
        data_extract[clean_key] = df

    return data_extract  # {'accounts': df, 'transactions': df}
```

</details>

---

### Step 2: Transform - Cleaning and Shaping Data

All common transformation logic lives in `Base_Transformer`, which both `Dim_Transformer` and `Fact_Transformer` inherit from:

<details>
<summary><b>📄 View code — <code>to_date()</code></b></summary>

```python
def to_date(self, df, columns: list):
    """Converts text date columns to datetime; invalid values become NaT."""
    for i in columns:
        if i in df.columns:
            df[i] = pd.to_datetime(df[i], errors='coerce')
        else:
            self.logger.warning(f"Column '{i}' not found in DataFrame.")
    return df
```

</details>

<details>
<summary><b>📄 View code — <code>convert_ns_to_us()</code></b></summary>

```python
def convert_ns_to_us(self, df, date_formatted_column):
    """Converts timestamp precision from ns to us so BigQuery accepts it."""
    if date_formatted_column in df.columns:
        df[date_formatted_column] = df[date_formatted_column].astype('datetime64[us]')
    return df
```

</details>

<details>
<summary><b>📄 View code — <code>create_date_key()</code></b></summary>

```python
def create_date_key(self, df, date_column, key_date='xxx_key_date'):
    """Creates an integer date key (e.g. 20240315) from a datetime column."""
    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df[key_date] = df[date_column].dt.strftime('%Y%m%d').astype(int)
    return df
```

</details>

<details>
<summary><b>📄 View code — <code>create_surrogate_key()</code></b></summary>

```python
def create_surrogate_key(self, df, selected_cols: list, new_key_name="new_key_name"):
    """Builds a composite key by concatenating values from multiple columns."""
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

<details>
<summary><b>📄 View code — <code>unflatten_list()</code></b></summary>

```python
def unflatten_list(self, df, list_col, col_to_keep):
    """Explodes a column of lists (e.g. line_items) into separate rows."""
    df_dict_version = df.to_dict(orient='records')
    df_items = pd.json_normalize(
        df_dict_version,
        record_path=list_col,
        meta=col_to_keep,
        errors='ignore'
    )
    return df_items
```

</details>

<details>
<summary><b>📄 View code — <code>data_quality_check()</code></b></summary>

```python
def data_quality_check(self, df, table_name, critical_null_columns=None,
                        key_columns=None, date_columns=None,
                        amount_columns=None, allow_negative_amounts=False):
    """
    Logs null counts, flags duplicates (is_deleted = 1), validates date
    ranges, and detects amount outliers using the IQR method.
    """
    null_counts = df.isnull().sum()
    ...

    df['is_deleted'] = 0
    if key_columns:
        valid_keys = [c for c in key_columns if c in df.columns]
        is_dup = df.duplicated(subset=valid_keys, keep='first')
        df.loc[is_dup, 'is_deleted'] = 1
    ...

    if amount_columns:
        for col in amount_columns:
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[col][(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
            if len(outliers) > 0:
                self.logger.warning(f"Column '{col}' has {len(outliers)} outliers (IQR method)")
    return df
```

</details>

<details>
<summary><b>📄 View code — <code>handle_missing_value()</code></b></summary>

```python
def handle_missing_value(self, df, fill_cols: dict = {}):
    """Fills specific null columns with safe defaults, e.g. {'customer_id': -1}."""
    for col, value in fill_cols.items():
        if col in df.columns:
            missing_count = df[col].isnull().sum()
            if missing_count > 0:
                df[col] = df[col].fillna(value)
                self.logger.info(f"Column {col} HAS FILLED {missing_count} values by '{value}'")
    return df
```

</details>

#### Dimension tables — built by `Dim_Transformer`

- `dim_customer` - customer profile from Shopify; `customer_segment`, `first_order_date`, `last_order_date` start empty and get filled in later by the SQL step
- `dim_product` - product catalogue from Shopify; `is_active` flag added
- `dim_location` - store locations from Sapo POS; `location_type` set to `Offline Store`

<details>
<summary><b>📄 View code — <code>transform_dim_customer()</code></b></summary>

```python
def transform_dim_customer(self, df):  # From Shopify data
    col_mapping = {
        'id': 'customer_id', 'email': 'email', 'name': 'full_name',
        'phone': 'phone', 'city': 'city', 'country': 'country',
        'created_at': 'created_at', 'total_spent_vnd': 'lifetime_value_vnd',
        'total_orders': 'total_orders'
    }
    selected_cols = [c for c in col_mapping.keys() if c in df.columns]
    df_dim = df[selected_cols].copy()
    df_dim.rename(columns=col_mapping, inplace=True)

    df_dim = self.to_date(df_dim, ['created_at'])

    # Placeholder columns, filled later by the RFM SQL step
    df_dim['customer_segment'] = 'Default'
    df_dim['first_order_date'] = pd.NaT
    df_dim['last_order_date'] = pd.NaT
    return df_dim
```

</details>

<details>
<summary><b>📄 View code — <code>transform_dim_product()</code></b></summary>

```python
def transform_dim_product(self, df):  # From Shopify data
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

<details>
<summary><b>📄 View code — <code>transform_dim_location()</code></b></summary>

```python
def transform_dim_location(self, df):  # From Sapo data (offline POS)
    col_mapping = {
        'id': 'location_id', 'code': 'location_code', 'name': 'location_name',
        'city': 'city', 'address': 'address', 'phone': 'phone'
    }
    selected_cols = [c for c in col_mapping.keys() if c in df.columns]
    df_dim = df[selected_cols].copy()
    df_dim.rename(columns=col_mapping, inplace=True)

    df_dim['location_type'] = 'Offline Store'
    df_dim['is_active'] = 1
    return df_dim
```

</details>

#### Fact tables — built by `Fact_Transformer`

- `fact_orders` - combines orders from Shopify, Online Orders, and Sapo POS. Each source is cleaned separately, then all three are stacked together using `pd.concat`
- `fact_order_items` - explodes the `line_items` array inside each order into individual product rows, then stacks all channels together
- `fact_payments` - standardises payment records from ZaloPay, MoMo, and PayPal. Each gateway uses a different success code - `return_code == 1` for ZaloPay, `resultCode == 0` for MoMo - both are mapped to `SUCCESS`/`FAILED`. **PayPal data was excluded from the final load due to very low data volume**, but the transformer is kept for future use.
- `fact_cart_events` - maps raw user behaviour events (*add to cart, view item, etc.*) with UTM tracking fields
- `fact_bank_transactions` - processes Mercury Bank records; negative amounts (outflows) are allowed and noted

<details>
<summary><b>📄 View code — <code>transform_fact_order()</code> (combines 3 channels)</b></summary>

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

    # Enforce dtypes to avoid BigQuery schema mismatches
    fact_order['total_vnd'] = fact_order['total_vnd'].fillna(0).astype('int64')
    fact_order['order_date_key'] = fact_order['order_date_key'].fillna(19000101).astype('int32')
    return fact_order
```

</details>

<details>
<summary><b>📄 View code — <code>fact_order_shopify()</code> (one of the 3 per-channel sub-transforms)</b></summary>

```python
def fact_order_shopify(self, df):
    col_mapping = {
        'id': 'order_id', 'transaction_id': 'transaction_id',
        'customer_id': 'customer_id', 'order_date': 'order_date',
        'source': 'source', 'payment_status': 'payment_status',
        'total_vnd': 'total_vnd', 'total_usd': 'total_usd'
    }
    selected_cols = [c for c in col_mapping.keys() if c in df.columns]
    fact_order_shopify = df[selected_cols].copy()
    fact_order_shopify.rename(columns=col_mapping, inplace=True)

    fact_order_shopify['status'] = None  # Shopify raw has no fulfillment status
    fact_order_shopify = self.to_date(fact_order_shopify, ['order_date'])
    fact_order_shopify = self.create_date_key(fact_order_shopify, 'order_date', 'order_date_key')

    fact_order_shopify['channel'] = 'shopify'
    fact_order_shopify = self.create_surrogate_key(
        fact_order_shopify, ['channel', 'order_id', 'transaction_id'], 'order_key'
    )
    return fact_order_shopify
```

</details>

<details>
<summary><b>📄 View code — <code>fact_order_items_shopify()</code> (exploding <code>line_items</code>)</b></summary>

```python
def fact_order_items_shopify(self, df, original_source):
    selected_cols = ['order_key', 'order_id', 'transaction_id', 'order_date_key']
    order_items = df[selected_cols].copy().merge(original_source, how='inner', on=['transaction_id'])
    order_items = order_items.rename(columns={'transaction_id': 'transaction_id_original'})

    # Flatten nested line_items array into relational rows
    exploded = self.unflatten_list(
        order_items[['order_key', 'order_date_key', 'transaction_id_original', 'line_items']],
        'line_items', ['order_key', 'order_date_key', 'transaction_id_original']
    )

    exploded = self.create_surrogate_key(exploded, ['order_key', 'product_id'], 'order_item_key')
    exploded['line_total_vnd'] = exploded['quantity'] * exploded['price']
    ...
    return exploded
```

</details>

<details>
<summary><b>📄 View code — payment-gateway success-code mapping (<code>fact_payment_zalopay</code> / <code>fact_payment_momo</code>)</b></summary>

```python
# ZaloPay: return_code == 1 → SUCCESS
fact_payment_zalopay['payment_status'] = np.where(
    df['return_code'] == 1, 'SUCCESS', 'FAILED'
)

# MoMo: resultCode == 0 → SUCCESS
fact_payment_momo['payment_status'] = np.where(
    df['resultCode'] == 0, 'SUCCESS', 'FAILED'
)
```

</details>

<details>
<summary><b>📄 View code — <code>transform_fact_cart_events()</code></b></summary>

```python
def transform_fact_cart_events(self, df):
    col_mapping = {
        'event_id': 'event_id', 'session_id': 'session_id', 'customer_id': 'customer_id',
        'event_type': 'event_type', 'timestamp': 'event_timestamp', 'product_id': 'product_id',
        'source': 'source', 'device': 'device', 'utm_source': 'utm_source',
        'utm_campaign': 'utm_campaign'
    }
    selected_cols = [c for c in col_mapping.keys() if c in df.columns]
    fact_cart_events = df[selected_cols].copy()
    fact_cart_events.rename(columns=col_mapping, inplace=True)

    fact_cart_events = self.to_date(fact_cart_events, ['event_timestamp'])
    fact_cart_events = self.create_date_key(fact_cart_events, 'event_timestamp', 'event_date_key')
    fact_cart_events = self.create_surrogate_key(fact_cart_events, ['event_type', 'event_id'], 'event_key')

    fact_cart_events = self.handle_missing_value(fact_cart_events, {
        'customer_id': '-1', 'product_id': '-1',
        'utm_source': 'unidentified', 'utm_campaign': 'unidentified'
    })
    return fact_cart_events
```

</details>

<details>
<summary><b>📄 View code — <code>transform_fact_bank_transactions()</code></b></summary>

```python
def transform_fact_bank_transactions(self, df):
    col_mapping = {
        'transaction_id': 'transaction_id', 'accountId': 'account_id',
        'kind': 'transaction_type', 'amount_vnd': 'amount_vnd', 'status': 'status',
        'createdAt': 'transaction_date', 'source': 'source'
    }
    selected_cols = [c for c in col_mapping.keys() if c in df.columns]
    fact_bank_transactions = df[selected_cols].copy()
    fact_bank_transactions.rename(columns=col_mapping, inplace=True)

    fact_bank_transactions = self.to_date(fact_bank_transactions, ['transaction_date'])
    fact_bank_transactions = self.create_date_key(
        fact_bank_transactions, 'transaction_date', 'transaction_date_key'
    )
    fact_bank_transactions = self.create_surrogate_key(
        fact_bank_transactions, ['source', 'transaction_id'], 'transaction_key'
    )
    return fact_bank_transactions
```

</details>

---

### Step 3: Load - Writing to BigQuery

`Big_Query_Loader` handles all writes to BigQuery. It automatically picks the right partition type based on the column:

- Date/timestamp columns → partition by day
- Integer date key columns (like `20240315`) → range partition

Each table is also **clustered** to make queries faster (e.g. `fact_orders` clusters on `customer_id` and `channel` so filtering by customer or channel is cheap). All tables use `WRITE_TRUNCATE` - the pipeline does a full reload each run.

<details>
<summary><b>📄 View code — auto-detecting partition type in <code>load_dataframe()</code></b></summary>

```python
def load_dataframe(self, df, dataset_id, bq_table_name,
                    write_disposition='WRITE_TRUNCATE',
                    partition_by=None, cluster_by=None):
    destination_table = f"{self.client.project}.{dataset_id}.{bq_table_name}"
    job_config = bigquery.LoadJobConfig(
        write_disposition=getattr(bigquery.WriteDisposition, write_disposition)
    )

    if partition_by:
        if partition_by in df.columns and pd.api.types.is_integer_dtype(df[partition_by]):
            # Integer date key (e.g. 20240101) → RangePartitioning
            job_config.range_partitioning = bigquery.RangePartitioning(
                field=partition_by,
                range_=bigquery.PartitionRange(start=19000101, end=21001231, interval=1)
            )
        else:
            # DATE / TIMESTAMP field → TimePartitioning
            job_config.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY, field=partition_by
            )

    if cluster_by:
        job_config.clustering_fields = cluster_by

    job = self.client.load_table_from_dataframe(df, destination_table, job_config=job_config)
    job.result()
```

</details>

<details>
<summary><b>📄 View code — example call from the orchestrator</b></summary>

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

---

### Step 4: SQL Update - Customer Segments (RFM)

After all tables are loaded, the pipeline runs a BigQuery `MERGE` statement that:

1. Pulls order history from `fact_orders` (paid + completed orders only) and calculates each customer's total spend, order count, first order date, and last order date
2. Scores each customer on **Recency, Frequency, and Monetary** value using `NTILE(5)` - giving each axis a score from 1 to 5
3. Combines the three scores into a 3-digit cell (e.g. `555`, `312`) and maps it to a segment name: *At Risk, Growing / Potential, Lost / Inactive, Needs Attention, No Purchase, and others*.
4. Customers with no purchase history are labelled `No Purchase` - their `total_orders = 0` and `first/last_order_date` remain `null`
5. Updates `dim_customer` in place - existing rows are overwritten with the new values

<details>
<summary><b>📄 View code — aggregating order history per customer</b></summary>

```sql
aggregate_value AS (
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

<details>
<summary><b>📄 View code — RFM scoring with <code>NTILE(5)</code></b></summary>

```sql
rfm_score AS (
    SELECT
        customer_id,
        last_order_date AS recency,
        total_orders AS frequency,
        life_time_value_vnd AS monetary,
        CONCAT(
            CAST(NTILE(5) OVER (ORDER BY last_order_date) AS STRING),
            CAST(NTILE(5) OVER (ORDER BY total_orders) AS STRING),
            CAST(NTILE(5) OVER (ORDER BY life_time_value_vnd) AS STRING)
        ) AS rfm_cell
    FROM aggregate_value
)
```

</details>

<details>
<summary><b>📄 View code — mapping RFM cell → segment name</b></summary>

```sql
CASE
    WHEN rfm_cell IN ('555','554','544','545',...)   THEN 'VIP / Best Customers'
    WHEN rfm_cell IN ('553','551','552','541',...)   THEN 'Growing / Potential'
    WHEN rfm_cell IN ('535','534','443','434',...)   THEN 'Needs Attention'
    WHEN rfm_cell IN ('331','321','312','221',...)   THEN 'At Risk'
    WHEN rfm_cell IN ('155','154','144','214',...)   THEN 'Lost / Inactive'
    ELSE 'Unknown'
END AS segment
```

</details>

---

### Step 5: Orchestration & Error Handling

`Pipeline_Orchestrator` runs everything in the right order:

```
check_dataset → process_dimensions() → process_facts() → execute_sql_query()
```

Each table has its own `try/except` block - if one source fails, the rest of the pipeline keeps running and logs the failure instead of crashing silently. Every step is logged to both the console and a log file via `setup_logger()`.

<details>
<summary><b>📄 View code — isolated try/except per table in <code>process_dimensions()</code></b></summary>

```python
def process_dimensions(self):
    self.logger.info('--- Starting Process: DIMENSION TABLES ---')

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
        raise e

    # dim_product and dim_location follow the same pattern, each in its own try/except...
```

</details>

<details>
<summary><b>📄 View code — <code>orchestrator_run()</code>, the single entry point</b></summary>

```python
def orchestrator_run(self):
    self.logger.info(">>> PIPELINE STARTED <<<")
    try:
        self.loader.check_dataset_available(self.dataset_id)
        self.process_dimensions()
        self.process_facts()
        self.execute_sql_query()
        self.logger.info(">>> PIPELINE FINISHED SUCCESSFULLY <<<")
    except Exception as e:
        self.logger.critical(f">>> PIPELINE FAILED: {e} <<<")
        raise e
```

</details>

---

## 🗄 Data Model (Star Schema)

![Star Schema Data Model](Images/Star_Schema_Data_Model.png)

*Figure 2: Star Schema*

Dimension tables describe the "who", "what", "where", and "when". Fact tables record what actually happened (orders, payments, events) and link back to dimensions via foreign keys.

### Dimension Tables

| Table | Source | Partition | Key Column | What It Contains |
|---|---|---|---|---|
| `dim_customer` | `Shopify` | `created_at` | `customer_id` | Customer profile + RFM segment, lifetime value, etc.. Updated automatically after each pipeline run. |
| `dim_product` | `Shopify` | - | `product_id` | Product name, SKU, category, etc. |
| `dim_location` | `Sapo POS` | - | `location_id` | Store name, code, city, address, phone. `location_type` = `Offline Store`. |
| `dim_date` | - | - | `date_key` | Date attributes: year, quarter, month, etc. |

> `dim_staff` was part of the original scope but **not built** - Sapo POS raw data does not include staff information.

### Fact Tables

| Table | Sources | Partition | Cluster | Primary Key | What It Records |
|---|---|---|---|---|---|
| `fact_orders` | `Shopify` · `Online Orders` · `Sapo POS` | `order_date_key` | `customer_id`, `channel` | `order_key` | Every order across all channels. |
| `fact_order_items` | `Shopify` · `Online Orders` · `Sapo POS` | `order_date_key` | `product_id` | `order_item_key` | Each product line inside an order. |
| `fact_payments` | `ZaloPay` · `MoMo` · `PayPal` | `payment_date_key` | `customer_id`, `payment_gateway` | `payment_key` | Payment transactions from e-wallet gateways. |
| `fact_cart_events` | `Cart Tracking` | `event_date_key` | `customer_id`, `session_id`, `event_type` | `event_key` | User actions on site. |
| `fact_bank_transactions` | `Mercury Bank` | `transaction_date_key` | - | `transaction_key` | Bank-level inflows and outflows. |

### Analytical Views

Three views sit on top of the fact tables and are ready to query directly from Power BI:

| View | Built From | What It Answers |
|---|---|---|
| `vw_customer_journey` | `fact_cart_events` + `fact_orders` | How did each customer move from first interaction to purchase?. |
| `vw_cashflow_daily` | `fact_orders` + `fact_payments` + `fact_bank_transactions` + `dim_date` | What came in and went out each day?. |
| `vw_payment_status` | `fact_orders` + `fact_payments` | Is each order actually paid?. |

> For full column details on all tables, see the 📄 [Data Dictionary](data_dictionary.md)

---

## 📊 BigQuery Output

The screenshots below show real query results from BigQuery after the pipeline has run.

### `dim_customer` - RFM Segments Auto-Updated

![dim_customer](Images/Dim_customer.png)

`dim_customer` is updated after every pipeline run via the BigQuery MERGE. The table shows each customer's recalculated `lifetime_value_vnd`, `total_orders`, `last_order_date`, and their current RFM segment - including `No Purchase` for customers with no order history (`total_orders = 0` and `first_order_date` / `last_order_date` left as `null`).

### `vw_cashflow_daily` - Daily Revenue and Cashflow

![vw_cashflow_daily](Images/vw_cashflow_daily.png)

`vw_cashflow_daily` brings together sales, payments, and bank records into one row per day. Finance can check whether revenue was actually collected without joining tables manually.

### `vw_customer_journey` - Touchpoint Sequence Per Customer

![vw_customer_journey](Images/vw_customer_journey.png)

`vw_customer_journey` shows each customer's path from first site interaction to purchase - including the full event sequence (e.g. `view_item > add_to_cart > purchase`) and how many hours it took.

### `vw_payment_status` - Payment Health Per Order

![vw_payment_status](Images/vw_payment_status.png)

`vw_payment_status` joins orders and payments to classify every order's payment health and flag overdue or partially paid orders.

---

## 📈 Power BI

The three analytical views (`vw_customer_journey`, `vw_cashflow_daily`, `vw_payment_status`) are connected to Power BI via the native BigQuery connector for future business reporting.

### Data Model View in Power BI

![Power BI Model View](Images/PBImodelview.png)

*Figure 3: The three views loaded into Power BI's model view.*

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

## 🔎 Conclusion & Business Impact

📍 **Key Outcomes:**

✔️ **One place for all data** - sales from Shopify, Sapo POS, and online channels; payments from MoMo, ZaloPay, PayPal, and Mercury; and user behaviour from cart tracking - all cleaned and in one BigQuery dataset.

✔️ **Faster reporting** - the analytics team gets clean, structured tables they can query directly. No more manual exports or fixing mismatched formats before each report.

✔️ **Daily cashflow visibility** - Finance can check whether money was actually received each day with a single query against `vw_cashflow_daily`.

✔️ **Always up-to-date customer segments** - Marketing gets fresh RFM segments automatically after every pipeline run, without a separate tool or manual step.

✔️ **Easy to extend** - adding a new data source only means writing a new extractor class. Everything else (cleaning logic, loader, orchestrator) stays the same.

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

