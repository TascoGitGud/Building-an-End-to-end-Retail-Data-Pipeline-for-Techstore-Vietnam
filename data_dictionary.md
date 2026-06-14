# Data Dictionary — TechStore Analytics

**Dataset:** `techstore_analytics`

---

## Dimension Tables

### dim_customers
Partition: `created_at`

| Column | Type | Description |
|---|---|---|
| customer_id | INT64 | Customer ID (PK) |
| email | STRING | Customer email |
| full_name | STRING | Full name |
| phone | STRING | Phone number |
| city | STRING | City |
| country | STRING | Country |
| created_at | TIMESTAMP | Account creation date |
| customer_segment | STRING | Customer segment (VIP, Regular, New, ...) |
| lifetime_value_vnd | NUMERIC | Customer lifetime value in VND |
| total_orders | INT64 | Total number of orders |
| first_order_date | TIMESTAMP | Date of first order |
| last_order_date | TIMESTAMP | Date of most recent order |

---

### dim_products

| Column | Type | Description |
|---|---|---|
| product_id | INT64 | Product ID (PK) |
| product_name | STRING | Product name |
| sku | STRING | SKU code |
| barcode | STRING | Barcode |
| category | STRING | Product category |
| brand | STRING | Brand |
| price_vnd | NUMERIC | Price in VND |
| price_usd | NUMERIC | Price in USD |
| stock_quantity | INT64 | Stock quantity |
| is_active | BOOL | Whether the product is active |

---

### dim_locations

| Column | Type | Description |
|---|---|---|
| location_id | INT64 | Location ID (PK) |
| location_code | STRING | Location code |
| location_name | STRING | Location name |
| location_type | STRING | Location type (store, warehouse, ...) |
| city | STRING | City |
| address | STRING | Address |
| phone | STRING | Phone number |
| is_active | BOOL | Whether the location is active |

---

### dim_date

| Column | Type | Description |
|---|---|---|
| date_key | DATE/INT64 | Date key (PK) |
| year | INT64 | Year |
| quarter | INT64 | Quarter (1-4) |
| month | INT64 | Month (1-12) |
| month_name | STRING | Month name |
| week | INT64 | Week number of the year |
| day_of_month | INT64 | Day of the month |
| day_of_week | INT64 | Day of the week (1-7) |
| day_name | STRING | Day name (Monday, Tuesday, ...) |
| is_weekend | BOOL | Whether the day is a weekend |
| is_holiday | BOOL | Whether the day is a holiday |
| fiscal_year | INT64 | Fiscal year |
| fiscal_quarter | INT64 | Fiscal quarter |

---

## Fact Tables

### fact_orders
Partition: `order_date_key` · Cluster: `customer_id`, `channel`

| Column | Type | Description |
|---|---|---|
| order_key | STRING/INT64 | Order key (PK) |
| order_id | STRING | Order ID from source system |
| transaction_id | STRING | Transaction ID linked to fact_payments |
| customer_id | INT64 | FK → dim_customers.customer_id |
| order_date | TIMESTAMP | Order timestamp |
| order_date_key | DATE/INT64 | FK → dim_date.date_key |
| channel | STRING | Sales channel (online, store, app, ...) |
| source | STRING | Order source |
| status | STRING | Order status (pending, completed, cancelled, refunded, ...) |
| payment_status | STRING | Payment status of the order |
| total_vnd | NUMERIC | Order total in VND |
| total_usd | NUMERIC | Order total in USD |

---

### fact_order_items
Partition: `order_date_key` · Cluster: `product_id`

| Column | Type | Description |
|---|---|---|
| order_item_key | STRING/INT64 | Order item key (PK) |
| order_key | STRING/INT64 | FK → fact_orders.order_key |
| transaction_id | STRING | Transaction ID |
| product_id | INT64 | FK → dim_products.product_id |
| quantity | INT64 | Quantity |
| unit_price_vnd | NUMERIC | Unit price in VND |
| line_total_vnd | NUMERIC | Line total = quantity × unit_price_vnd |

---

### fact_payments
Partition: `payment_date_key` · Cluster: `customer_id`, `payment_gateway`

| Column | Type | Description |
|---|---|---|
| payment_key | STRING/INT64 | Payment key (PK) |
| transaction_id | STRING | FK → fact_orders.transaction_id |
| order_id | STRING | FK → fact_orders.order_id |
| customer_id | INT64 | FK → dim_customers.customer_id |
| payment_gateway | STRING | Payment gateway (Momo, VNPay, Stripe, ...) |
| payment_method | STRING | Payment method (card, bank_transfer, cod, ...) |
| amount_vnd | NUMERIC | Transaction amount in VND |
| payment_status | STRING | Payment status (success, failed, refunded, pending) |
| payment_date | TIMESTAMP | Transaction timestamp |
| payment_date_key | DATE/INT64 | FK → dim_date.date_key |

---

### fact_cart_events
Partition: `event_date_key` · Cluster: `customer_id`, `session_id`, `event_type`

| Column | Type | Description |
|---|---|---|
| event_key | STRING/INT64 | Event key (PK) |
| event_id | STRING | Original event ID |
| session_id | STRING | Session ID |
| customer_id | INT64 | FK → dim_customers.customer_id |
| event_type | STRING | Event type: add_to_cart, remove_from_cart, view_item, purchase, etc. |
| event_timestamp | TIMESTAMP | Event timestamp |
| event_date_key | DATE/INT64 | FK → dim_date.date_key |
| product_id | INT64 | FK → dim_products.product_id |
| source | STRING | Traffic source |
| device | STRING | Device type (mobile, desktop, tablet) |
| browser | STRING | Browser |
| utm_source | STRING | UTM source (marketing tracking) |
| utm_campaign | STRING | UTM campaign (marketing tracking) |

---

### fact_bank_transactions
Partition: `transaction_date_key`

| Column | Type | Description |
|---|---|---|
| transaction_key | STRING/INT64 | Transaction key (PK) |
| transaction_id | STRING | Bank transaction ID |
| account_id | STRING | Bank account ID |
| transaction_type | STRING | inflow or outflow |
| amount_vnd | NUMERIC | Amount in VND |
| status | STRING | Status (completed, pending, failed) |
| transaction_date | TIMESTAMP | Transaction timestamp |
| transaction_date_key | DATE/INT64 | FK → dim_date.date_key |

---

## Views for Analysis

### vw_customer_journey

| Column | Type | Description |
|---|---|---|
| customer_id | INT64 | Customer ID |
| touchpoint_seq | INT64 | Sequence number of the touchpoint |
| event_type | STRING | Event type or "purchase" |
| event_timestamp | TIMESTAMP | Event timestamp |
| session_id | STRING | Session ID (NULL for purchase rows) |
| product_id | INT64 | Related product (NULL for purchase rows) |
| source | STRING | Traffic source |
| device | STRING | Device type |
| utm_source | STRING | UTM source |
| utm_campaign | STRING | UTM campaign |
| order_id | STRING | Order ID (purchase rows only) |
| order_total_vnd | NUMERIC | Order total (purchase rows only) |
| first_touchpoint_at | TIMESTAMP | Customer's first touchpoint |
| first_purchase_at | TIMESTAMP | Customer's first purchase timestamp |
| hours_to_first_purchase | INT64 | Hours from first touchpoint to first purchase |
| touchpoint_sequence | STRING | Cumulative event sequence joined by ">" |

---

### vw_cashflow_daily

| Column | Type | Description |
|---|---|---|
| date_key | DATE/INT64 | Report date |
| year | INT64 | Year |
| month | INT64 | Month |
| month_name | STRING | Month name |
| day_name | STRING | Day of week name |
| is_weekend | BOOL | Whether the day is a weekend |
| sales_revenue_vnd | NUMERIC | Sales revenue for the day |
| total_orders | INT64 | Number of valid orders for the day |
| payment_received_vnd | NUMERIC | Total successful payments received |
| payment_refunded_vnd | NUMERIC | Total refunded amount |
| total_payment_transactions | INT64 | Number of payment transactions |
| bank_inflow_vnd | NUMERIC | Total bank inflow |
| bank_outflow_vnd | NUMERIC | Total bank outflow |
| net_bank_cashflow_vnd | NUMERIC | bank_inflow_vnd - bank_outflow_vnd |
| net_cashflow_vnd | NUMERIC | (payment_received - payment_refunded) + (bank_inflow - bank_outflow) |

---

### vw_payment_status

| Column | Type | Description |
|---|---|---|
| order_key | STRING/INT64 | Order key |
| order_id | STRING | Order ID |
| transaction_id | STRING | Transaction ID |
| customer_id | INT64 | FK → dim_customers.customer_id |
| order_date | TIMESTAMP | Order timestamp |
| channel | STRING | Sales channel |
| order_status | STRING | Order status |
| order_payment_status | STRING | Payment status recorded on the order |
| order_total_vnd | NUMERIC | Order total |
| total_paid_vnd | NUMERIC | Total amount successfully paid |
| outstanding_amount_vnd | NUMERIC | Remaining amount owed |
| first_success_payment_date | TIMESTAMP | Timestamp of first successful payment |
| last_payment_date | TIMESTAMP | Timestamp of most recent payment |
| last_payment_gateway | STRING | Most recent payment gateway |
| last_payment_method | STRING | Most recent payment method |
| payment_delay_hours | INT64 | Hours from order placement to successful payment |
| payment_status_category | STRING | Paid, Pending, Overdue, Partially Paid, Cancelled, Unknown |
