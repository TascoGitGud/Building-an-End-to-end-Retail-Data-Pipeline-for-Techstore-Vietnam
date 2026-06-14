import pandas as pd
import numpy as np
from transformers.base_transformer import Base_Transformer

class Fact_Transformer(Base_Transformer):
    def __init__(self):
        super().__init__()
 
    # fact_payments
    # ZaloPay
    def fact_payment_zalopay(self, df):
        
        #select column and set a new name:
        col_mapping = {
            'transaction_id': 'transaction_id',
            'app_trans_id': 'order_id',
            'customer_id': 'customer_id',
            'source': 'payment_gateway',
            'amount': 'amount_vnd',
            'server_time_iso': 'payment_date'
        }

        #create fact_payment_zalopay and rename columns
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        fact_payment_zalopay = df[selected_cols].copy()
        
        fact_payment_zalopay.rename(columns = col_mapping, inplace=True)
        
        # Set up
        fact_payment_zalopay['payment_status'] = np.where(
            df['return_code'] == 1,
            'SUCCESS',
            'FAILED'
        )
        fact_payment_zalopay['payment_method'] = 'e-wallet'

        #convert to datetime
        fact_payment_zalopay = self.to_date(fact_payment_zalopay, ['payment_date'])

        #convert ns to us
        fact_payment_zalopay = self.convert_ns_to_us(fact_payment_zalopay, 'payment_date')

        #create payment_date_key
        fact_payment_zalopay = self.create_date_key(fact_payment_zalopay, 'payment_date', 'payment_date_key')

        #create payment_key
        fact_payment_zalopay = self.create_surrogate_key(fact_payment_zalopay, ['payment_gateway', 'transaction_id'], 'payment_key')

        #bring payment key into 1st column
        new_col_order = ['payment_key'] + [c for c in fact_payment_zalopay.columns if c != 'payment_key']
        fact_payment_zalopay = fact_payment_zalopay[new_col_order]
        
        return fact_payment_zalopay

    # MoMo
    def fact_payment_momo(self, df):
       
        #select column and set a new name:
        col_mapping = {
            'transaction_id': 'transaction_id',
            'orderId': 'order_id',
            'source':'payment_gateway',
            'amount': 'amount_vnd',
            'responseTimeISO' : 'payment_date',
            'payType':'payment_method'
        }

        #create fact_payment_momo and rename columns
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        fact_payment_momo = df[selected_cols].copy()
        
        fact_payment_momo.rename(columns = col_mapping, inplace=True)
        # MoMo raw data does not contain customer_id
        fact_payment_momo['customer_id'] = None
        fact_payment_momo['payment_status'] = np.where(
            df['resultCode'] == 0,
            'SUCCESS',
            'FAILED'
        )
        #convert to datetime
        fact_payment_momo = self.to_date(fact_payment_momo, ['payment_date'])

         #convert ns to us
        fact_payment_momo = self.convert_ns_to_us(fact_payment_momo, 'payment_date')

        #create payment_date_key
        fact_payment_momo = self.create_date_key(fact_payment_momo, 'payment_date', 'payment_date_key')

        #create payment_key
        fact_payment_momo = self.create_surrogate_key(fact_payment_momo, ['payment_gateway', 'transaction_id'], 'payment_key')

        #bring payment key into 1st column
        new_col_order = ['payment_key'] + [c for c in fact_payment_momo.columns if c != 'payment_key']
        fact_payment_momo = fact_payment_momo[new_col_order]
        
        return fact_payment_momo
    
    # PayPal
    def fact_payment_paypal(self, df):
       
        #select column and set a new name:
        col_mapping = {
            'transaction_id': 'transaction_id',
            'paypal_transaction_id': 'order_id',
            'customer_id':'customer_id',
            'source':'payment_gateway',
            'transaction_amount_vnd': 'amount_vnd',
            'transaction_status' : 'payment_status',
            'transaction_initiation_date' : 'payment_date'
        }

        #create fact_payment_paypal and rename columns
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        fact_payment_paypal = df[selected_cols].copy()
        
        fact_payment_paypal.rename(columns = col_mapping, inplace=True)

        #create payment_method: due to there is no payment_method infomation available in data raw, so I label it "e-wallet"
        fact_payment_paypal['payment_method'] = 'e-wallet'

        #convert to datetime
        fact_payment_paypal = self.to_date(fact_payment_paypal, ['payment_date'])

        #convert ns to us
        fact_payment_paypal = self.convert_ns_to_us(fact_payment_paypal, 'payment_date')

        #create payment_date_key
        fact_payment_paypal = self.create_date_key(fact_payment_paypal, 'payment_date', 'payment_date_key')

        #create payment_key
        fact_payment_paypal = self.create_surrogate_key(fact_payment_paypal, ['payment_gateway', 'transaction_id'], 'payment_key')

        #bring payment key into 1st column
        new_col_order = ['payment_key'] + [c for c in fact_payment_paypal.columns if c != 'payment_key']
        fact_payment_paypal = fact_payment_paypal[new_col_order]
        
        return fact_payment_paypal
    
    def transform_fact_payment(self, df_zalopay, df_momo, df_paypal):
        """
        Create fact_payment table by combining and standardizing data from multiple payment gateways (ZaloPay, MoMo, PayPal).
        """
        # Transform each source's payment data into a standardized format
        f_zalopay = self.fact_payment_zalopay(df_zalopay)
        f_momo = self.fact_payment_momo(df_momo)
        f_paypal = self.fact_payment_paypal(df_paypal)

        # Concat 3 payment data into a single fact_payment df
        fact_payment = pd.concat([f_zalopay, f_momo, f_paypal], ignore_index=True)

        # standardize column order before loading to data warehouse
        standard_cols = [
            'payment_key',
            'transaction_id',
            'order_id',
            'customer_id',
            'payment_gateway',
            'payment_method',
            'amount_vnd',
            'payment_status',
            'payment_date',
            'payment_date_key'
        ]

        final_cols = [c for c in standard_cols if c in fact_payment.columns]
        fact_payment = fact_payment[final_cols]

        if 'amount_vnd' in fact_payment.columns:
            fact_payment['amount_vnd'] = fact_payment['amount_vnd'].fillna(0).astype('int64')
        if 'payment_date_key' in fact_payment.columns:
            fact_payment['payment_date_key'] = fact_payment['payment_date_key'].fillna(19000101).astype('int32')

        return fact_payment

    # fact_order
    # Shopify
    def fact_order_shopify(self, df):

        # Select column and set a new name:
        col_mapping = {
            'id': 'order_id',
            'transaction_id': 'transaction_id',
            'customer_id':'customer_id',
            'order_date':'order_date',
            'source':'source',
            'payment_status':'payment_status',  # keep as payment_status
            'total_vnd':'total_vnd',
            'total_usd':'total_usd'
        }

        # Create fact_order_shopify and rename columns
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        fact_order_shopify = df[selected_cols].copy()

        fact_order_shopify.rename(columns = col_mapping, inplace = True)
        
        # Shopify raw does not have order fulfillment status → set None
        fact_order_shopify['status'] = None

        # Format date
        fact_order_shopify = self.to_date(fact_order_shopify, ['order_date'])

        # Convert ns to us 
        fact_order_shopify = self.convert_ns_to_us(fact_order_shopify, 'order_date')

        # Create order_date_key
        fact_order_shopify = self.create_date_key(fact_order_shopify, 'order_date', key_date ='order_date_key')
        # Fix source and channel values
        fact_order_shopify['channel'] = 'shopify'
        fact_order_shopify = self.create_surrogate_key(fact_order_shopify, ['channel', 'order_id', 'transaction_id'], 'order_key')
        
        # Bring order_key into 1st column
        new_col_order = ['order_key'] + [c for c in fact_order_shopify.columns if c != 'order_key']
        fact_order_shopify = fact_order_shopify[new_col_order]

        return fact_order_shopify
    
    # Order Online
    def fact_order_online(self, df):

        #select column and set a new name:
        col_mapping = {
            'order_id': 'order_id',
            'transaction_id': 'transaction_id',
            'customer_id':'customer_id',
            'created_at':'order_date',
            'channel':'channel',
            'status':'status',
            'total':'total_vnd',
        }

        # Create fact_order_online and rename columns
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        fact_order_online = df[selected_cols].copy()
        fact_order_online.rename(columns = col_mapping, inplace = True)
        
        fact_order_online['source'] = 'order_online'
        # Online orders raw does not have payment_status
        fact_order_online['payment_status'] = None
        fact_order_online = self.to_date(fact_order_online, ['order_date'])

        # Convert ns to us 
        fact_order_online = self.convert_ns_to_us(fact_order_online, 'order_date')

        # Create order_date_key
        fact_order_online = self.create_date_key(fact_order_online, 'order_date', key_date = 'order_date_key')

        # Calculate total_usd to vnd
        fact_order_online['total_usd'] = round((fact_order_online['total_vnd'] / 26255), 2)  #1 usd = 26255 vnd 

        # Create orderkey
        fact_order_online = self.create_surrogate_key(fact_order_online, ['channel', 'order_id', 'transaction_id'], 'order_key')

        # Bring order_key into 1st column
        new_col_order = ['order_key'] + [c for c in fact_order_online.columns if c != 'order_key']
        fact_order_online = fact_order_online[new_col_order]
        
        return fact_order_online
    
    # Sapo
    def fact_order_sapo(self, df):
        """
        Transform and standardize raw Sapo POS orders data.
        """

        # Map flat fields from the raw Sapo data schema
        col_mapping = {
            'id': 'order_id',
            'transaction_id': 'transaction_id',
            'source': 'source',
            'status': 'status',
            'total_vnd': 'total_vnd'
        }

        # Filter available columns and clone data
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        fact_order_sapo = df[selected_cols].copy()
        fact_order_sapo.rename(columns=col_mapping, inplace=True)

        # Extract customer_id from nested 'customer' object if available
        if 'customer' in df.columns:
            fact_order_sapo['customer_id'] = df['customer'].apply(
                lambda x: x.get('id') if isinstance(x, dict) else np.nan
            )
        elif 'customer_id' in df.columns:
            fact_order_sapo['customer_id'] = df['customer_id']
        else:
            fact_order_sapo['customer_id'] = np.nan

        # Handle date field mapping 
        sapo_date_col = 'created_at' if 'created_at' in df.columns else ('order_date' if 'order_date' in df.columns else None)
        if sapo_date_col:
            fact_order_sapo['order_date'] = df[sapo_date_col]
        else:
            fact_order_sapo['order_date'] = pd.Timestamp.now()

        # Format date string to datetime object
        fact_order_sapo = self.to_date(fact_order_sapo, ['order_date'])

        # Convert timestamp precision from nanoseconds (ns) to microseconds (us)
        fact_order_sapo = self.convert_ns_to_us(fact_order_sapo, 'order_date')

        # Create order_date_key for Date Dimension mapping
        fact_order_sapo = self.create_date_key(fact_order_sapo, 'order_date', key_date ='order_date_key')
        # Set default values for offline POS channel attributes
        fact_order_sapo['channel'] = 'Offline_Stores'
        # Sapo POS raw does not have payment_status
        fact_order_sapo['payment_status'] = None
        if 'total_vnd' in fact_order_sapo.columns:
            fact_order_sapo['total_usd'] = round((fact_order_sapo['total_vnd'] / 26255), 2)
        else:
            fact_order_sapo['total_usd'] = 0.0

        # Generate primary surrogate key for fact table matching other sources
        fact_order_sapo = self.create_surrogate_key(fact_order_sapo, ['channel', 'order_id', 'transaction_id'], 'order_key')

        # Move order_key to the first column position
        new_col_order = ['order_key'] + [c for c in fact_order_sapo.columns if c != 'order_key']
        fact_order_sapo = fact_order_sapo[new_col_order]

        return fact_order_sapo
    
    # Combine all sources to create fact_order
    def transform_fact_order(self, df_shopify, df_online, df_sapo):
        """
        Combine and integrate all standardized order data sources into a unified Fact table.
        """
        # Execute individual sub-transformations to reconcile data structures
        f_shopify = self.fact_order_shopify(df_shopify)
        f_online = self.fact_order_online(df_online)
        f_sapo = self.fact_order_sapo(df_sapo)

        # Concatenate standardized sources vertically
        fact_order = pd.concat([f_shopify, f_online, f_sapo], ignore_index=True)

        # Define explicit Data Warehouse target schema column ordering
        standard_cols = [
            'order_key',
            'order_id',
            'transaction_id',
            'customer_id',
            'order_date',
            'order_date_key',
            'channel',
            'source',
            'status',
            'payment_status',
            'total_vnd',
            'total_usd'
        ]

        # Rearrange columns and discard unmapped internal properties
        final_cols = [c for c in standard_cols if c in fact_order.columns]
        fact_order = fact_order[final_cols]

        # Enforce definitive data types to prevent BigQuery schema mismatches
        if 'total_vnd' in fact_order.columns:
            fact_order['total_vnd'] = fact_order['total_vnd'].fillna(0).astype('int64')
        if 'total_usd' in fact_order.columns:
            fact_order['total_usd'] = fact_order['total_usd'].fillna(0.0).astype('float64')
        if 'order_date_key' in fact_order.columns:
            fact_order['order_date_key'] = fact_order['order_date_key'].fillna(19000101).astype('int32')

        return fact_order

    # Fact Order Items
    # Shopify
    def fact_order_items_shopify(self, df, original_source):
        """
        Transform and standardize Shopify order items.
        """
        # Get identifier columns from cleaned orders table
        selected_cols = ['order_key', 'order_id', 'transaction_id', 'order_date_key']
        order_items_shopify = df[selected_cols].copy()

        # Join back with raw source data to extract line items array
        order_items_shopify = order_items_shopify.merge(original_source, how='inner', on=['transaction_id'])

        # Rename transaction_id to avoid duplication conflicts during merge
        order_items_shopify = order_items_shopify.rename(columns={'transaction_id':'transaction_id_original'})
        
        # Remove unnecessary columns
        keep_cols = ['order_key', 'order_date_key', 'transaction_id_original', 'line_items']
        order_items_shopify = order_items_shopify[keep_cols]

        # Flatten nested JSON list in 'line_items' into relational rows
        exploded_order_items_shopify = self.unflatten_list(order_items_shopify, 'line_items', ['order_key', 'order_date_key','transaction_id_original'])
        
        # Dynamically identify child product ID column (id / product_id)
        id_col = 'product_id' if 'product_id' in exploded_order_items_shopify.columns else \
                 ('id' if 'id' in exploded_order_items_shopify.columns else 'item_id')

        # Generate unique primary key for item level
        exploded_order_items_shopify = self.create_surrogate_key(exploded_order_items_shopify, ['order_key', id_col], 'order_item_key')
        
        # Use purchase quantity instead of product stock quantity
        qty_col = 'quantity' if 'quantity' in exploded_order_items_shopify.columns else 'stock_quantity'

        # Dynamically locate item price column inside line_items
        shopify_price_col = 'price' if 'price' in exploded_order_items_shopify.columns else \
                            ('price_vnd' if 'price_vnd' in exploded_order_items_shopify.columns else 'unit_price')

        # Calculate line total based on actual quantity and item price
        if 'line_total_vnd' not in exploded_order_items_shopify.columns:
            exploded_order_items_shopify['line_total_vnd'] = exploded_order_items_shopify[qty_col] * exploded_order_items_shopify[shopify_price_col]

        # Map current columns to target Data Warehouse schema
        col_mapping = {
            'order_item_key': 'order_item_key',
            'order_key': 'order_key',
            'order_date_key': 'order_date_key',
            'transaction_id_original': 'transaction_id', 
            id_col: 'product_id',                         
            qty_col: 'quantity',                          
            shopify_price_col: 'unit_price_vnd',          
            'line_total_vnd': 'line_total_vnd',
        }

        final_col = [c for c in col_mapping.keys() if c in exploded_order_items_shopify.columns]
        fact_order_items_shopify = exploded_order_items_shopify[final_col].copy()
        fact_order_items_shopify.rename(columns=col_mapping, inplace=True)

        return fact_order_items_shopify

    # Order Online
    def fact_order_items_online(self, df, original_source):
        """
        Transform and standardize Multi-channel Online order items.
        """
        # Get identifier columns from cleaned orders table
        selected_cols = ['order_key', 'order_id', 'transaction_id', 'order_date_key']
        order_items_online = df[selected_cols].copy()

        # Join back with raw source data using transaction_id
        order_items_online = order_items_online.merge(original_source, how='inner', on=['transaction_id'])

        # Rename transaction_id to avoid duplication conflicts during merge
        order_items_online = order_items_online.rename(columns={'transaction_id':'transaction_id_original'})
        
        keep_cols = ['order_key', 'order_date_key', 'transaction_id_original', 'line_items']
        order_items_online = order_items_online[keep_cols]

        # Flatten nested JSON list in 'line_items' into relational rows
        exploded_order_items_online = self.unflatten_list(order_items_online, 'line_items', ['order_key','order_date_key' ,'transaction_id_original'])
        
        # Dynamically identify child product ID column to prevent KeyError
        id_col = 'product_id' if 'product_id' in exploded_order_items_online.columns else \
                 ('id' if 'id' in exploded_order_items_online.columns else \
                 ([c for c in exploded_order_items_online.columns if 'id' in c][0] if [c for c in exploded_order_items_online.columns if 'id' in c] else 'item_id'))
        
        # Generate unique primary key for item level
        exploded_order_items_online = self.create_surrogate_key(exploded_order_items_online, ['order_key', id_col], 'order_item_key')
        
        # Dynamically locate item price column
        online_price_col = 'unit_price' if 'unit_price' in exploded_order_items_online.columns else \
                           ('price' if 'price' in exploded_order_items_online.columns else 'price_vnd')
        
        # Calculate line total if not present in raw data
        if 'line_total' not in exploded_order_items_online.columns and online_price_col in exploded_order_items_online.columns:
            exploded_order_items_online['line_total'] = exploded_order_items_online['quantity'] * exploded_order_items_online[online_price_col]
        elif 'line_total_vnd' in exploded_order_items_online.columns:
            exploded_order_items_online['line_total'] = exploded_order_items_online['line_total_vnd']

        # Map current columns to target Data Warehouse schema
        col_mapping = {
            'order_item_key': 'order_item_key',
            'order_key': 'order_key',
            'order_date_key': 'order_date_key',
            'transaction_id_original': 'transaction_id',
            id_col: 'product_id', 
            'quantity': 'quantity', 
            online_price_col: 'unit_price_vnd', 
            'line_total': 'line_total_vnd', 
        }

        final_col = [c for c in col_mapping.keys() if c in exploded_order_items_online.columns]
        fact_order_items_online = exploded_order_items_online[final_col].copy()
        fact_order_items_online.rename(columns=col_mapping, inplace=True)

        return fact_order_items_online
    
    # Sapo POS
    def fact_order_items_sapo(self, df, original_source):
        """
        Transform and standardize Sapo POS order items by unflattening nested objects.
        Updated based on exact Sapo schema: orders contain 'line_items' array.
        """
        # Select identifier columns from cleaned fact_order_sapo
        selected_cols = ['order_key', 'order_id', 'transaction_id', 'order_date_key']
        order_items_sapo = df[selected_cols].copy()

        # Merge with original source to get line_items 
        if 'transaction_id' in original_source.columns and order_items_sapo['transaction_id'].notnull().any():
            order_items_sapo = order_items_sapo.merge(original_source, how='inner', on=['transaction_id'])
        else:
            # Sapo uses code or id
            raw_id_col = 'code' if 'code' in original_source.columns else 'id'
            order_items_sapo = order_items_sapo.merge(original_source, how='inner', left_on=['order_id'], right_on=[raw_id_col])

        # Rename transaction_id
        order_items_sapo = order_items_sapo.rename(columns={'transaction_id':'transaction_id_original'})
        
        # Keep only necessary columns 
        keep_cols = ['order_key', 'order_date_key', 'transaction_id_original', 'line_items']
        order_items_sapo = order_items_sapo[keep_cols]

        # Expand the nested JSON list inside 'line_items' column into separate relational rows
        exploded_order_items_sapo = self.unflatten_list(order_items_sapo, 'line_items', ['order_key', 'order_date_key','transaction_id_original'])
        
        # Generate item-level surrogate primary key
        id_col = 'id' if 'id' in exploded_order_items_sapo.columns else ([c for c in exploded_order_items_sapo.columns if 'id' in c][0] if [c for c in exploded_order_items_sapo.columns if 'id' in c] else 'product_id')
        exploded_order_items_sapo = self.create_surrogate_key(exploded_order_items_sapo, ['order_key', id_col], 'order_item_key')
        
        # Calculate line_total if not already present
        sapo_price_col = 'price_vnd' if 'price_vnd' in exploded_order_items_sapo.columns else ('price' if 'price' in exploded_order_items_sapo.columns else 'unit_price')
        if 'line_total_vnd' not in exploded_order_items_sapo.columns and sapo_price_col in exploded_order_items_sapo.columns:
            exploded_order_items_sapo['line_total_vnd'] = exploded_order_items_sapo['quantity'] * exploded_order_items_sapo[sapo_price_col]

        # Map current columns to target Data Warehouse schema
        col_mapping = {
            'order_item_key': 'order_item_key',
            'order_key': 'order_key',
            'order_date_key': 'order_date_key',
            'transaction_id_original': 'transaction_id', 
            id_col: 'product_id',                         
            'quantity': 'quantity',
            sapo_price_col: 'unit_price_vnd',             
            'line_total_vnd': 'line_total_vnd',
        }

        final_col = [c for c in col_mapping.keys() if c in exploded_order_items_sapo.columns]
        fact_order_items_sapo = exploded_order_items_sapo[final_col].copy()
        fact_order_items_sapo.rename(columns=col_mapping, inplace=True)

        return fact_order_items_sapo

    # Combine:
    def transform_fact_order_items(self, df_shopify, df_online, df_sapo):
        """
        Combine and integrate all channel-specific order items data sources into a unified Fact table.
        Gracefully handles empty or missing DataFrames from channels without item-level details.
       """
        # Collect non-empty and valid DataFrames for vertical concatenation
        dfs_to_concat = []
        for df in [df_shopify, df_online, df_sapo]:
            if df is not None and not df.empty:
                dfs_to_concat.append(df)
                
        # Return an empty schema-compliant template if no operational data exists
        if not dfs_to_concat:
            self.logger.warning("All input Order Items DataFrames are empty. Returning empty DataFrame.")
            return pd.DataFrame()

        # Concatenate all stream segments vertically along the rows
        fact_order_items = pd.concat(dfs_to_concat, ignore_index=True)

        # Enforce target Data Warehouse schema mapping for Fact Order Items
        standard_cols = [
            'order_item_key',
            'order_key',
            'order_date_key',
            'transaction_id',
            'product_id',
            'quantity',
            'unit_price_vnd',
            'line_total_vnd'
        ]

        # Filter out irrelevant columns and maintain the explicit dimensional order
        final_cols = [c for c in standard_cols if c in fact_order_items.columns]
        fact_order_items = fact_order_items[final_cols]

        # Enforce strict downstream data type constraints (BigQuery/Snowflake compliance)
        if 'quantity' in fact_order_items.columns:
            fact_order_items['quantity'] = fact_order_items['quantity'].fillna(0).astype('int64')
        if 'unit_price_vnd' in fact_order_items.columns:
            fact_order_items['unit_price_vnd'] = fact_order_items['unit_price_vnd'].fillna(0).astype('int64')
        if 'line_total_vnd' in fact_order_items.columns:
            fact_order_items['line_total_vnd'] = fact_order_items['line_total_vnd'].fillna(0).astype('int64')
        if 'order_date_key' in fact_order_items.columns:
            fact_order_items['order_date_key'] = fact_order_items['order_date_key'].fillna(19000101).astype('int32')

        self.logger.info(f"Successfully integrated Fact Order Items. Final shape: {fact_order_items.shape}")
        return fact_order_items
   
    # Fact Cart Events
    def transform_fact_cart_events(self, df):
        #select column and set a new name:
        col_mapping = {
            'event_id': 'event_id',
            'session_id': 'session_id',
            'customer_id':'customer_id',
            'event_type':'event_type',
            'timestamp':'event_timestamp',
            'product_id':'product_id',
            'source':'source',
            'device':'device',
            'utm_source':'utm_source',
            'utm_campaign':'utm_campaign'
        }

        # Create fact_cart_event and rename columns
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        fact_cart_events = df[selected_cols].copy()

        fact_cart_events.rename(columns = col_mapping, inplace = True)

        #format date
        fact_cart_events = self.to_date(fact_cart_events, ['event_timestamp'])

        #creat event_date_key
        fact_cart_events = self.create_date_key(fact_cart_events, 'event_timestamp', 'event_date_key')

        #convert ns to us
        fact_cart_events = self.convert_ns_to_us(fact_cart_events, 'event_timestamp')

        #tạo event_key
        fact_cart_events = self.create_surrogate_key(fact_cart_events, ['event_type', 'event_id'], 'event_key')

        #đảo event_key lên đầu
        new_col_order = ['event_key'] + [c for c in fact_cart_events.columns if c != 'event_key']
        fact_cart_events = fact_cart_events[new_col_order]

        #handle missing value
        fact_cart_events = self.handle_missing_value(fact_cart_events,
                                                     {'customer_id' : '-1',
                                                      'product_id': '-1',
                                                      'utm_source': 'unidentified',
                                                      'utm_campaign': 'unidentified'})
        
        fact_cart_events['customer_id'] = fact_cart_events['customer_id'].astype('int64')
        fact_cart_events['product_id'] = fact_cart_events['product_id'].astype('int64')
        
        return fact_cart_events

    # Fact Bank Transactions
    def transform_fact_bank_transactions(self, df):
        # Select column and set a new name:
        col_mapping = {
            'transaction_id': 'transaction_id',
            'accountId': 'account_id',
            'kind':'transaction_type',
            'amount_vnd':'amount_vnd',
            'status':'status',
            'createdAt':'transaction_date',
            'source':'source'
        }

        # Create fact_bank_transactions and rename columns
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        fact_bank_transactions = df[selected_cols].copy()

        fact_bank_transactions.rename(columns = col_mapping, inplace = True)

        # Format date
        fact_bank_transactions = self.to_date(fact_bank_transactions, ['transaction_date'])

        # Create transaction_date_key
        fact_bank_transactions = self.create_date_key(fact_bank_transactions, 'transaction_date', 'transaction_date_key')

        # Create transaction_key
        fact_bank_transactions = self.create_surrogate_key(fact_bank_transactions, ['source', 'transaction_id'], 'transaction_key')
        
        # Bring transaction_key to the front
        new_col_order = ['transaction_key'] + [c for c in fact_bank_transactions.columns if c != 'transaction_key']
        fact_bank_transactions = fact_bank_transactions[new_col_order]
        
        return fact_bank_transactions



# if __name__ == '__main__':
#     import os
#     import sys
#     import pandas as pd
#     import numpy as np
#     import warnings

#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     project_root = os.path.dirname(current_dir) # Lùi 1 cấp thư mục
#     sys.path.append(project_root)

#     from extractors.shopify_extractor import Shopify_Extractor
#     from extractors.online_extractor import Online_Extractor
#     from extractors.sapo_extractor import Sapo_Extractor  # Đảm bảo đã import Sapo
#     from utils.logger import setup_logger

#     from transformers.fact_transformer import Fact_Transformer

#     bucket = 'your-bucket-name'  # Replace with your actual bucket name
#     fact_table = Fact_Transformer()

#     # 1. Initialize data extractors for all three operational channels
#     shopify_ext = Shopify_Extractor(bucket)
#     online_ext = Online_Extractor(bucket)
#     sapo_ext = Sapo_Extractor(bucket)         

#     # 2. Extract raw dataframes from Google Cloud Storage buckets
#     shopify_raw = shopify_ext.extract_file()
#     online_raw = online_ext.extract_file()
#     sapo_raw = sapo_ext.extract_file()        

#     print("\n--- Execution Started: Transforming Fact Orders ---")
#     # 3. Reconcile and unify multi-channel data into the global Fact Orders table
#     fact_order = fact_table.transform_fact_order(shopify_raw, online_raw, sapo_raw)
#     print(f"-> Fact Orders Transformation Complete. Shape: {fact_order.shape}")

#     print("\n--- Execution Started: Extracting Channel-Specific Order Items ---")
#     # Generate intermediate standardized order tables required for foreign key mapping
#     f_order_shopify_reconciled = fact_table.fact_order_shopify(shopify_raw)
#     f_order_online_reconciled = fact_table.fact_order_online(online_raw)
#     f_order_sapo_reconciled = fact_table.fact_order_sapo(sapo_raw)

#     # Flatten and parse item arrays for Shopify and Online Multi-channel streams
#     fact_order_items_shopify = fact_table.fact_order_items_shopify(f_order_shopify_reconciled, shopify_raw)
#     fact_order_items_online = fact_table.fact_order_items_online(f_order_online_reconciled, online_raw)

#     # FAIL-SAFE GUARD: Validate the existence of nested arrays before execution
#     # Sapo source often yields accounting files (accounts/transactions) without product lines.
#     # If 'line_items' is absent, initialize an empty DataFrame to bypass KeyError.
#     if 'line_items' in sapo_raw.columns:
#         fact_order_items_sapo = fact_table.fact_order_items_sapo(f_order_sapo_reconciled, sapo_raw)
#     else:
#         print("[WARNING] 'line_items' missing in raw Sapo schema. Generating an empty mock template.")
#         fact_order_items_sapo = pd.DataFrame(columns=fact_order_items_shopify.columns)

#     print("\n--- Execution Started: Merging All Order Items Streams ---")
#     # 4. Integrate processed item tables using the newly refactored 3-parameter function
#     fact_order_items = fact_table.transform_fact_order_items(
#         fact_order_items_shopify, 
#         fact_order_items_online, 
#         fact_order_items_sapo
#     )
#     print(f"-> Fact Order Items Integration Complete. Shape: {fact_order_items.shape}")
    
#     # 5. Output visual samples to verify Data Warehouse schema conformity
#     print("\n[SAMPLE DATA] Fact Orders:")
#     print(fact_order.head(2))
#     print("\n[SAMPLE DATA] Fact Order Items:")
#     print(fact_order_items.head(2))