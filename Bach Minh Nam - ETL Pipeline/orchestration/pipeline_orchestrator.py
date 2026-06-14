import pandas as pd
import os
import sys


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) 
sys.path.append(project_root)

from utils.logger import setup_logger

# Import Extractors
from extractors.sapo_extractor import Sapo_Extractor
from extractors.shopify_extractor import Shopify_Extractor
from extractors.payment_extractor import Payment_Extractor
from extractors.tracking_extractor import Tracking_Extractor
from extractors.online_extractor import Online_Extractor

# Import Transformers
from transformers.dimension_transformer import Dim_Transformer
from transformers.fact_transformer import Fact_Transformer

# Import Loaders
from loaders.bigquery_loader import Big_Query_Loader


class Pipeline_Orchestrator:
    """
    The Orchestrator class responsible for managing the End-to-End ETL Pipeline.
    It coordinates the Extraction, Transformation, and Loading (ETL) phases
    for both Dimension and Fact tables.
    """

    def __init__(self, bucket_name, dataset_id):
        self.logger = setup_logger(__name__)

        self.bucket_name = bucket_name
        self.dataset_id = dataset_id

        # Initialize Transformers
        self.dim_transformer = Dim_Transformer()
        self.fact_transformer = Fact_Transformer()
        
        # Initialize Loaders
        self.loader = Big_Query_Loader()
        
        
    def process_dimensions(self):
        """
        Orchestrates the ETL process for all Dimension Tables.
        Current implementation: Dim_Customer, Dim_Product.
        """
        self.logger.info('--- Starting Process: DIMENSION TABLES ---')  
        
        #Process DIM_CUSTOMER
        try:
            self.logger.info("Processing 'dim_customer'...")
            
            #Extract
            extractor = Shopify_Extractor(self.bucket_name)
            customer_data_raw = extractor.extract_file()

            #Transform
            dim_customer = self.dim_transformer.transform_dim_customer(customer_data_raw)

            #Data quality check
            self.dim_transformer.data_quality_check(
                df= dim_customer,
                table_name= 'dim_customer',
            )

            #Loader
            self.loader.load_dataframe(
                df= dim_customer,
                dataset_id= self.dataset_id,
                partition_by= 'created_at',
                bq_table_name= 'dim_customer',
            )
            
            self.logger.info("Finished 'dim_customer'.")

        except Exception as e:
            self.logger.critical(f'Fail when processing DIM_CUSTOMER: {e}')
            raise e
        
        #Process DIM_PRODUCT
        try:
            self.logger.info("Processing 'dim_product'...")
            
            #Extract
            extractor = Shopify_Extractor(self.bucket_name)
            product_data_raw = extractor.extract_file()

            #Transform
            dim_product = self.dim_transformer.transform_dim_product(product_data_raw)

            #Data quality check
            self.dim_transformer.data_quality_check(
                df= dim_product,
                table_name= 'dim_product',
            )

            #Loader
            self.loader.load_dataframe(
                df= dim_product,
                dataset_id= self.dataset_id,
                bq_table_name= 'dim_product',
            )
            
            self.logger.info("Finished 'dim_product'.")

        except Exception as e:
            self.logger.critical(f'Fail when processing dim_product: {e}')
            raise e
        
        #Process DIM_LOCATION
        try:
            self.logger.info("Processing 'dim_locations'...")
            
            #Extract
            extractor = Sapo_Extractor(self.bucket_name)
            location_data_raw = extractor.extract_file()

            #Transform
            dim_location = self.dim_transformer.transform_dim_location(location_data_raw)

            #Data quality check
            self.dim_transformer.data_quality_check(
                df= dim_location,
                table_name= 'dim_location',
            )

            #Loader
            self.loader.load_dataframe(
                df= dim_location,
                dataset_id= self.dataset_id,
                partition_by= 'created_at',
                bq_table_name= 'dim_location',
            )
            
            self.logger.info("Finished 'dim_location'.")

        except Exception as e:
            self.logger.critical(f'Fail when processing DIM_LOCATION: {e}')
            raise e
        
    def process_facts(self):
        """
        Orchestrates the ETL process for all Fact Tables.
        Current implementation: 
            - Fact_Orders (Merged from Shopify & Online).
            - Fact_Order_Items (Merged from Shopify & Online)
            - Fact_Order_Payement (Merged from Zalopay and Momo)
                * Note: Due to seriously lacking data, we decided to remove all data from PayPal source. 
                For details: see ... in the Report.
            - Fact_Cart_Event
            - Fact_Bank_Transaction
        """
        self.logger.info('--- Starting Process: FACT TABLES ---')
        
        #Process FACT_ORDERS
        try:
            self.logger.info("Processing 'fact_orders'...")
            #EXTRACT
            # Extract shopify
            shopify = Shopify_Extractor(self.bucket_name)
            shopify_data_raw = shopify.extract_file()

            # Extract online_orders
            online_orders = Online_Extractor(self.bucket_name)
            online_orders_data_raw = online_orders.extract_file()

            # Extract sapo_orders
            sapo = Sapo_Extractor(self.bucket_name)
            sapo_data_raw = sapo.extract_file()

            #TRANSFORM
            # transform_fact_orders() calls fact_orders_shopify/online/sapo internally
            # so pass raw data directly — do NOT pre-transform to avoid double transformation
            fact_orders = self.fact_transformer.transform_fact_orders(shopify_data_raw, online_orders_data_raw, sapo_data_raw)

            #Loader
            self.loader.load_dataframe(
                df= fact_orders,
                dataset_id= self.dataset_id,
                bq_table_name= 'fact_orders',
                write_disposition= 'WRITE_TRUNCATE',
                partition_by= 'order_date_key',
                cluster_by= ['customer_id', 'channel']
            )
            self.logger.info("Finished 'fact_orders'.")

        except Exception as e:
            self.logger.critical(f'Fail when processing FACT_ORDERS: {e}')
            raise e
        
        
        #Process FACT_ORDER_ITEMS
        try:
            self.logger.info("Processing 'fact_order_items'...")
            #EXTRACT
            # Extract shopify
            shopify = Shopify_Extractor(self.bucket_name)
            shopify_data_raw = shopify.extract_file()

            # Extract online_orders
            online_orders = Online_Extractor(self.bucket_name)
            online_orders_data_raw = online_orders.extract_file()

            # Extract sapo_orders
            sapo = Sapo_Extractor(self.bucket_name)
            sapo_data_raw = sapo.extract_file()

            #TRANSFORM
            fact_shopify_orders = self.fact_transformer.fact_orders_shopify(shopify_data_raw)
            fact_shopify_order_items = self.fact_transformer.fact_order_items_shopify(fact_shopify_orders, shopify_data_raw)
            
            fact_online_orders = self.fact_transformer.fact_orders_online(online_orders_data_raw)
            fact_online_order_items = self.fact_transformer.fact_order_items_online(fact_online_orders, online_orders_data_raw)

            fact_sapo_orders = self.fact_transformer.fact_orders_sapo(sapo_data_raw)
            fact_sapo_order_items = self.fact_transformer.fact_order_items_sapo(fact_sapo_orders, sapo_data_raw)

            # Union table
            fact_order_items = self.fact_transformer.transform_fact_order_items(fact_shopify_order_items, fact_online_order_items, fact_sapo_order_items)

            #Data quality check
            self.fact_transformer.data_quality_check(
                df= fact_order_items,
                table_name= 'fact_order_items',
            )
            
            #Loader
            self.loader.load_dataframe(
                df= fact_order_items,
                dataset_id= self.dataset_id,
                bq_table_name= 'fact_order_items',
                write_disposition= 'WRITE_TRUNCATE',
                partition_by= 'order_date_key',
                cluster_by= ['product_id']
            )
            self.logger.info("Finished 'fact_order_items'.")
            
        except Exception as e:
            self.logger.critical(f'Fail when processing fact_order_items: {e}')
            raise e
        
        #Process FACT_PAYMENT
        try:
            self.logger.info("Processing 'fact_payment'...")
            #EXTRACT
    
            payement = Payment_Extractor(self.bucket_name)
            momo_data_raw = payement.payment_momo_extract()
            zalopay_data_raw = payement.payment_zalopay_extract()
            paypal_data_raw = payement.payment_paypal_extract()
             

            # transform_fact_payment() calls fact_payment_* internally
            # so pass raw data directly — do NOT pre-transform to avoid double transformation
            fact_payment = self.fact_transformer.transform_fact_payment(zalopay_data_raw, momo_data_raw, paypal_data_raw)

            #Data quality check
            self.fact_transformer.data_quality_check(
                df= fact_payment,
                table_name= 'fact_payment',
            )

            #Loader
            self.loader.load_dataframe(
                df= fact_payment,
                dataset_id= self.dataset_id,
                bq_table_name= 'fact_payment',
                write_disposition= 'WRITE_TRUNCATE',
                partition_by= 'payment_date_key',
                cluster_by= ['customer_id', 'payment_gateway']
            )
            self.logger.info("Finished 'fact_payment'.")
            
        except Exception as e:
            self.logger.critical(f'Fail when processing fact_payment: {e}')
            raise e
        
        #Process FACT_BANK_TRANSACTIONS

        try:
            self.logger.info("Processing 'fact_bank_transactions'...")
            #EXTRACT
            payement = Payment_Extractor(self.bucket_name)
            bank_transactions_data_raw = payement.payment_mercury_extract()['transactions']  # payment_mercury_extract() returns dict {'accounts': df, 'transactions': df}

            #TRANSFORM
            fact_bank_transactions = self.fact_transformer.transform_fact_bank_transactions(bank_transactions_data_raw)

            #Data quality check
            self.fact_transformer.data_quality_check(
                df= fact_bank_transactions,
                table_name= 'fact_bank_transactions',
                allow_negative_amounts= True,
            )

            #Loader
            self.loader.load_dataframe(
                df= fact_bank_transactions,
                dataset_id= self.dataset_id,
                bq_table_name= 'fact_bank_transactions',
                partition_by= 'transaction_date_key',
                write_disposition= 'WRITE_TRUNCATE'
            )
            self.logger.info("Finished 'fact_bank_transactions'.")
            
        except Exception as e:
            self.logger.critical(f'Fail when processing fact_bank_transactions: {e}')
            raise e


        #Process FACT_CART_EVENTS
        try:
            self.logger.info("Processing 'fact_cart_events'...")
            #EXTRACT
            tracking = Tracking_Extractor(self.bucket_name)
            cart_events_data_raw = tracking.extract_file()
          
            #TRANSFORM
            fact_cart_events = self.fact_transformer.transform_fact_cart_events(cart_events_data_raw)

            #Data quality check
            self.fact_transformer.data_quality_check(
                df= fact_cart_events,
                table_name= 'fact_cart_events',
            )

            #Loader
            self.loader.load_dataframe(
                df= fact_cart_events,
                dataset_id= self.dataset_id,
                bq_table_name= 'fact_cart_events',
                partition_by= 'event_date_key',
                cluster_by=['customer_id', 'session_id', 'event_type'],
                write_disposition= 'WRITE_TRUNCATE'
            )
            self.logger.info("Finished 'fact_cart_events'.")
            
        except Exception as e:
            self.logger.critical(f'Fail when processing fact_cart_events: {e}')
            raise e
        
    

    def execute_sql_query(self):

        self.logger.info(">>> STARTING SQL EXECUTE")

        aggregate_value_update = f"""
        MERGE `name_of_your_dataset.dim_customer` AS target
        USING (

            WITH aggregate_value AS ( -- Calculated aggregate value
                SELECT 
                    customer_id,
                    MIN(order_date) AS first_order_date,
                    MAX(order_date) AS last_order_date,
                    COUNT(DISTINCT order_key) AS total_orders, -- count order_key vì order_id có hiện tượng trùng ID
                    SUM(total_vnd) AS life_time_value_vnd
                FROM `name_of_your_dataset.fact_orders`
                WHERE payment_status IN ('paid', 'partially_paid')
                    AND status IN ('completed', 'shipping', 'delivered', 'fulfilled', 'pending')
                GROUP BY customer_id
            ),

            rfm_score AS ( -- calculate RFM score
                SELECT 
                    customer_id,
                    last_order_date AS recency,
                    total_orders AS frequency,
                    life_time_value_vnd AS monetary,
                    NTILE(5) OVER (ORDER BY last_order_date) AS r_score,
                    NTILE(5) OVER (ORDER BY total_orders) AS f_score,
                    NTILE(5) OVER (ORDER BY life_time_value_vnd) AS m_score,
                    CONCAT(
                        CAST(NTILE(5) OVER (ORDER BY last_order_date) AS STRING),
                        CAST(NTILE(5) OVER (ORDER BY total_orders) AS STRING),
                        CAST(NTILE(5) OVER (ORDER BY life_time_value_vnd) AS STRING)
                    ) AS rfm_cell
                FROM aggregate_value
            ),

            rfm_segment AS ( -- Segment based on RFM score
                SELECT 
                    r.customer_id,
                    a.first_order_date,
                    a.last_order_date,
                    a.total_orders,
                    a.life_time_value_vnd,
                    CASE
                        -- VIP / Best Customers  
                        WHEN rfm_cell IN (
                            '555','554','544','545','454','455','445',
                            '543','444','435','355','354','345','344','335'
                        ) THEN 'VIP / Best Customers'

                        -- Growing / Potential  
                        WHEN rfm_cell IN (
                            '553','551','552','541','542','533','532','531','452','451','442','441','431','453','433','432','423','353','352','351','342','341','333','323',
                            '512','511','422','421','412','411','311',
                            '525','524','523','522','521','515','514','513','425','424','413','414','415','315','314','313'
                        ) THEN 'Growing / Potential'

                        -- Needs Attention  
                        WHEN rfm_cell IN (
                            '535','534','443','434','343','334','325','324'
                        ) THEN 'Needs Attention'

                        -- At Risk  
                        WHEN rfm_cell IN (
                            '331','321','312','221','213','231','241','251',
                            '255','254','245','244','253','252','243','242','235','234','225','224','153','152','145','143','142','135','134','133','125','124'
                        ) THEN 'At Risk'

                        -- Lost / Inactive  
                        WHEN rfm_cell IN (
                            '155','154','144','214','215','115','114','113',
                            '332','322','233','232','223','222','132','123','122','212','211',
                            '111','112','121','131','141','151'
                        ) THEN 'Lost / Inactive'

                        ELSE 'Unknown'
                    END AS segment
                FROM rfm_score r
                LEFT JOIN aggregate_value a
                    ON r.customer_id = a.customer_id
            )

            -- FULL OUTER JOIN with all customers in dim_customer:
            -- anyone with no order history gets 'No Purchase'
            SELECT
                d.customer_id,
                s.first_order_date,
                s.last_order_date,
                COALESCE(s.total_orders, 0) AS total_orders,
                s.life_time_value_vnd,
                COALESCE(s.segment, 'No Purchase') AS segment
            FROM `name_of_your_dataset.dim_customer` d
            LEFT JOIN rfm_segment s
                ON d.customer_id = s.customer_id

        ) AS source

        ON target.customer_id = source.customer_id
        WHEN MATCHED THEN
        UPDATE SET
            target.first_order_date = source.first_order_date,
            target.last_order_date = source.last_order_date,
            target.total_orders = source.total_orders,
            target.life_time_value_vnd = source.life_time_value_vnd,
            target.customer_segment = source.segment;
        """
        try:
            self.logger.info(" Executing SQL query: Updating buying aggregate value and customer's segment")
            self.loader.execute_query(aggregate_value_update)

        except Exception as e:
            self.logger.critical(f"Failed to execute SQL: {e}")
            raise e
        


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
