# 📖 Raw Data Dictionary - TechStore Analytics
---

## 🛍️ E-commerce Platforms

### 🟢 Shopify (Online Store)

Location: `shopify/`

#### `products.json.gz`

~1,000 products

| Column           | Type    | Description          |
| ---------------- | ------- | --------------------- |
| `id`              | INT64   | Product ID (PK)        |
| `name`            | STRING  | Product name           |
| `sku`             | STRING  | SKU code               |
| `category`        | STRING  | Product category       |
| `brand`           | STRING  | Brand                  |
| `price_vnd`       | INT64   | Price in VND            |
| `price_usd`       | FLOAT64 | Price in USD            |
| `barcode`         | STRING  | Barcode                |
| `stock_quantity`  | INT64   | Stock quantity          |

---

#### `orders_batch_*.json.gz`

~200,000 orders

| Column           | Type      | Description                       |
| ---------------- | --------- | ---------------------------------- |
| `id`              | INT64     | Order ID (PK)                       |
| `order_number`    | STRING    | Order number                        |
| `transaction_id`  | STRING    | Linked payment transaction ID        |
| `customer_id`     | INT64     | FK → `customers.id`                  |
| `order_date`      | TIMESTAMP | Order timestamp                     |
| `payment_gateway` | STRING    | Payment gateway used                 |
| `payment_status`  | STRING    | Payment status                      |
| `total_vnd`       | INT64     | Order total in VND                   |
| `total_usd`       | FLOAT64   | Order total in USD                   |
| `line_items`      | ARRAY     | Array of order line items            |
| `source`          | STRING    | Fixed value: `"shopify"`             |

---

#### `staff.json.gz`

~300 staff members

> ⚠️ Required per spec, not found in bucket.

---

#### `customers_batch_*.json.gz`

~2,000,000 customers

| Column        | Type      | Description           |
| -------------- | --------- | ----------------------- |
| `id`            | INT64     | Customer ID (PK)         |
| `email`         | STRING    | Customer email           |
| `name`          | STRING    | Customer name            |
| `phone`         | STRING    | Phone number             |
| `city`          | STRING    | City                     |
| `country`       | STRING    | Country                  |
| `created_at`    | TIMESTAMP | Account creation date     |

---

### 🟣 Sapo POS (Offline Stores)

Location: `sapo/`

#### `locations.json.gz`

~50 stores

| Column      | Type   | Description       |
| ------------ | ------ | ------------------- |
| `id`          | INT64  | Location ID (PK)     |
| `code`        | STRING | Location code        |
| `name`        | STRING | Location name        |
| `address`     | STRING | Address              |
| `city`        | STRING | City                 |
| `phone`       | STRING | Phone number         |

---

#### `orders_batch_*.json.gz`

~1,000,000 orders

| Column           | Type   | Description                     |
| ----------------- | ------ | --------------------------------- |
| `id`               | INT64  | Order ID (PK)                       |
| `code`             | STRING | Order code                          |
| `transaction_id`   | STRING | Linked payment transaction ID        |
| `location_id`      | INT64  | FK → `locations.id`                  |
| `location_name`    | STRING | Store location name                  |
| `customer`         | OBJECT | Embedded customer object             |
| `staff`            | OBJECT | Embedded staff object                |
| `line_items`       | ARRAY  | Array of order line items            |
| `total_vnd`        | INT64  | Order total in VND                   |
| `payment_method`   | STRING | Payment method                      |
| `status`           | STRING | Order status                        |
| `source`           | STRING | Fixed value: `"sapo_pos"`            |

---

### 🌐 Online Orders (Multi-channel)

Location: `online_orders/`

#### `online_orders.json.gz`

~50,000 orders

| Column              | Type      | Description                                              |
| -------------------- | --------- | ----------------------------------------------------------- |
| `order_id`            | STRING    | Order ID (PK)                                                |
| `transaction_id`      | STRING    | Linked payment transaction ID                                 |
| `channel`             | STRING    | Channel: `shopify`, `website`, `mobile_app`, `lazada`, `shopee` |
| `customer_id`         | INT64     | FK → customer ID                                              |
| `status`              | STRING    | Order status                                                  |
| `line_items`          | ARRAY     | Array of order line items                                     |
| `total`               | INT64     | Order total                                                   |
| `payment_method`      | STRING    | Payment method                                                |
| `shipping_address`    | OBJECT    | Shipping address details                                       |
| `tracking`            | OBJECT    | Shipment tracking details                                      |
| `created_at`          | TIMESTAMP | Order creation timestamp                                       |

---

## 💳 Payment Gateways

### 🅿️ PayPal

Location: `paypal/`

#### `transactions.json.gz`

~300 transactions

| Column                       | Type      | Description                          |
| ----------------------------- | --------- | --------------------------------------- |
| `transaction_id`               | STRING    | Internal transaction ID (PK)             |
| `paypal_transaction_id`        | STRING    | PayPal-issued transaction ID              |
| `customer_id`                  | INT64     | FK → customer ID                         |
| `transaction_amount`           | OBJECT    | `{ currency_code, value }`                |
| `transaction_amount_vnd`       | INT64     | Transaction amount in VND                  |
| `transaction_status`           | STRING    | Transaction status                       |
| `payer_info`                   | OBJECT    | Payer details                            |
| `transaction_initiation_date`  | TIMESTAMP | Transaction initiation timestamp           |
| `source`                       | STRING    | Fixed value: `"paypal"`                   |

---

### 🏦 Mercury Bank

Location: `mercury/`

#### `accounts.json.gz`

~3 accounts

> ⚠️ Required per spec, not found in bucket.

---

#### `transactions.json.gz`

~500 transactions

| Column           | Type      | Description                                       |
| ----------------- | --------- | ---------------------------------------------------- |
| `id`               | STRING    | Transaction ID (PK)                                    |
| `transaction_id`   | STRING    | Transaction ID reference                              |
| `accountId`        | STRING    | FK → `accounts.id`                                     |
| `amount`           | FLOAT64   | Transaction amount                                    |
| `amount_vnd`       | INT64     | Transaction amount in VND                              |
| `kind`             | STRING    | Transaction kind |
| `status`           | STRING    | Transaction status                                    |
| `createdAt`        | TIMESTAMP | Transaction timestamp                                  |
| `details`          | OBJECT    | Additional transaction details                         |
| `source`           | STRING    | Fixed value: `"mercury_bank"`                          |

---

### 🟠 MoMo

Location: `gs://minpy/momo/`

#### `transactions.json.gz`

~500 transactions

| Column              | Type      | Description                        |
| --------------------- | --------- | -------------------------------------- |
| `transaction_id`       | STRING    | Internal transaction ID (PK)             |
| `orderId`              | STRING    | Order ID reference                       |
| `transId`              | INT64     | MoMo-issued transaction ID                |
| `amount`               | INT64     | Transaction amount                       |
| `resultCode`           | INT64     | Result code (`0` = success)               |
| `message`              | STRING    | Result message                          |
| `payType`              | STRING    | Payment type                            |
| `responseTime`         | INT64     | Response time (epoch)                    |
| `responseTimeISO`      | TIMESTAMP | Response timestamp (ISO format)           |
| `extraData`            | OBJECT    | Additional metadata                      |
| `source`               | STRING    | Fixed value: `"momo"`                    |

---

### 🔵 ZaloPay

Location: `zalopay/`

#### `transactions.json.gz`

~500 transactions

| Column              | Type      | Description                  |
| --------------------- | --------- | -------------------------------- |
| `transaction_id`       | STRING    | Internal transaction ID (PK)       |
| `app_trans_id`         | STRING    | App-side transaction ID             |
| `zp_trans_id`          | INT64     | ZaloPay-issued transaction ID        |
| `amount`               | INT64     | Transaction amount                  |
| `return_code`          | INT64     | Return code (`1` = success)          |
| `channel`              | INT64     | Payment channel code                 |
| `bank_code`            | STRING    | Bank code                           |
| `server_time_iso`      | TIMESTAMP | Server timestamp (ISO format)        |
| `refund_history`       | ARRAY     | Array of refund records              |
| `source`               | STRING    | Fixed value: `"zalopay"`             |

---

## 📈 Tracking & Analytics

### 🛒 Cart Tracking

Location: `cart_tracking/`

#### `cart_events.json.gz`

~10,000+ events

| Column          | Type      | Description                                                    |
| ----------------- | --------- | ------------------------------------------------------------------- |
| `event_id`         | STRING    | Event ID (PK)                                                       |
| `event_type`       | STRING    | Event type |
| `session_id`       | STRING    | Session ID                                                          |
| `customer_id`      | INT64     | Customer ID (`null` for guest users)                                  |
| `product_id`       | INT64     | FK → product ID                                                      |
| `timestamp`        | TIMESTAMP | Event timestamp                                                      |
| `source`           | STRING    | Event source                                                        |
| `device`           | STRING    | Device type                                                         |
| `browser`          | STRING    | Browser                                                             |
| `utm_source`       | STRING    | UTM source                                                          |
| `utm_campaign`     | STRING    | UTM campaign                                                        |

---

## 📦 Raw Source Summary

| Source           | GCS Path                       | File(s)                                          | Approx. Volume     |
| ------------------ | --------------------------------- | --------------------------------------------------- | --------------------- |
| Shopify             | `shopify/`              | `products`, `orders_batch_*`, `staff`, `customers_batch_*` | 1K products · 200K orders · 300 staff · 2M customers |
| Sapo POS            | `sapo/`                 | `locations`, `orders_batch_*`                        | 50 stores · 1M orders   |
| Online Orders        | `online_orders/`        | `online_orders`                                      | 50K orders              |
| PayPal               | `paypal/`               | `transactions`                                       | 300 transactions         |
| Mercury Bank         | `mercury/`              | `accounts`, `transactions`                            | 3 accounts · 500 transactions |
| MoMo                 | `momo/`                 | `transactions`                                       | 500 transactions         |
| ZaloPay              | `zalopay/`              | `transactions`                                       | 500 transactions         |
| Cart Tracking         | `cart_tracking/`        | `cart_events`                                        | 10K+ events             |
