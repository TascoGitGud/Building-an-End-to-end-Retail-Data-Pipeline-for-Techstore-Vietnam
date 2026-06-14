import pandas as pd
import numpy as np
from io import StringIO
from transformers.base_transformer import Base_Transformer

class Dim_Transformer(Base_Transformer):
    def __init__(self):
        super().__init__()

    def transform_dim_customer(self, df): # From Shopify data 
        '''
        Transform customer data into dimension table with attributes such as customer_id, email, full_name, phone, city, country, created_at, lifetime_value_vnd, total_orders, customer_segment, first_order_date, last_order_date, ...
        '''

        # Set new column names
        col_mapping = {
            'id': 'customer_id',
            'email': 'email',
            'name':'full_name',
            'phone':'phone',
            'city':'city',
            'country':'country',
            'created_at':'created_at',
            'total_spent_vnd':'lifetime_value_vnd',
            'total_orders':'total_orders'
        }

        # Create dim_customer table
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        df_dim = df[selected_cols].copy()

        # Rename columns
        df_dim.rename(columns = col_mapping, inplace = True)

        # Change dtype
        df_dim = self.to_date(df_dim, ['created_at'])

        # Create new columns
        df_dim['customer_segment'] = 'Default'
        df_dim['first_order_date'] = pd.NaT
        df_dim['last_order_date'] = pd.NaT

        return df_dim

    def transform_dim_product(self, df): # From Shopify data
        '''
        Transform product data into dimension table with attributes such as product_id, product_name, sku, barcode, category, brand, price_vnd, price_usd, stock_quantity, ...
        '''
        # Set new column names
        col_mapping = {
            'id': 'product_id',
            'name': 'product_name',
            'sku':'sku',
            'barcode':'barcode',
            'category':'category',
            'brand':'brand',
            'price_vnd':'price_vnd',
            'price_usd':'price_usd',
            'stock_quantity':'stock_quantity'
        }

        # Create dim_product table
        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        df_dim = df[selected_cols].copy()

        # Rename columns
        df_dim.rename(columns = col_mapping, inplace = True)

        # Create new columns
        df_dim['is_active'] = 1

        return df_dim
    
    def transform_dim_location(self, df): # From Sapo data cus is pos
        """
        Transform location data into dimension table with attributes such as location_id, location_code, location_name, city, address, phone, ...
        """
        
        col_mapping = {
            'id': 'location_id',
            'code': 'location_code',
            'name': 'location_name',
            'city': 'city',
            'address': 'address',
            'phone': 'phone'
        }

        selected_cols = [c for c in col_mapping.keys() if c in df.columns]
        df_dim = df[selected_cols].copy()
        df_dim.rename(columns=col_mapping, inplace=True)

        df_dim['location_type'] = 'Offline Store'
        df_dim['is_active'] = 1

        return df_dim

    # no staff data in sapo, skip transform_dim_staff
    # def transform_dim_staff(self, df): # From Sapo data cus is pos
    #     """
    #     Transform staff data into dimension table with attributes such as staff_id, staff_code, full_name, position, email, phone, location_id, hire_date, ...
    #     """
        
    #     col_mapping = {
    #         'staff_id': 'staff_id',
    #         'staff_code': 'staff_code',
    #         'full_name': 'full_name',
    #         'position': 'position',
    #         'email': 'email',
    #         'phone': 'phone',
    #         'location_id': 'location_id',
    #         'hire_date': 'hire_date'
    #     }

    #     selected_cols = [c for c in col_mapping.keys() if c in df.columns]
    #     df_dim = df[selected_cols].copy()
    #     df_dim.rename(columns=col_mapping, inplace=True)

    #     if 'hire_date' in df_dim.columns:
    #         df_dim = self.to_date(df_dim, ['hire_date'])

    #     df_dim['is_active'] = 1

    #     return df_dim

    # def transform_dim_date(self, start_date_str='1900-01-01', end_date_str='2100-12-31'):
    #     """
    #     Date dimension with attributes such as date_key, year, quarter, month, month_name, week, ...
    #     """
        
    #     date_range = pd.date_range(start=start_date_str, end=end_date_str, freq='D')
    #     df_dim = pd.DataFrame(date_range, columns=['date'])

    #     df_dim['date_key'] = df_dim['date'].dt.strftime('%Y%m%d').astype(int)
    #     df_dim['year'] = df_dim['date'].dt.year
    #     df_dim['quarter'] = df_dim['date'].dt.quarter
    #     df_dim['month'] = df_dim['date'].dt.month
    #     df_dim['month_name'] = df_dim['date'].dt.strftime('%B')
    #     df_dim['week'] = df_dim['date'].dt.isocalendar().week.astype(int)
    #     df_dim['day_of_month'] = df_dim['date'].dt.day
    #     df_dim['day_of_week'] = df_dim['date'].dt.dayofweek + 1  # monday=1, sunday=7
    #     df_dim['day_name'] = df_dim['date'].dt.strftime('%A')
        
    #     df_dim['is_weekend'] = np.where(df_dim['day_of_week'].isin([6, 7]), 1, 0)
        
    #     df_dim['is_holiday'] = 0
    #     df_dim['fiscal_year'] = df_dim['year']
    #     df_dim['fiscal_quarter'] = df_dim['quarter']

    #     df_dim.drop(columns=['date'], inplace=True)

    #     return df_dim


# if __name__ == '__main__':
#     import os
#     import sys

#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     project_root = os.path.dirname(current_dir)
#     sys.path.append(project_root)

#     from extractors.shopify_extractor import Shopify_Extractor
#     from extractors.payment_extractor import Payment_Extractor
#     from extractors.sapo_extractor import Sapo_Extractor
#     from extractors.online_extractor import Online_Extractor
#     from extractors.tracking_extractor import Tracking_Extractor    
#     from transformers.dimension_transformer import Dim_Transformer

#     bucket = 'minpy'

#     Shopify = Shopify_Extractor(bucket)
#     Shopify_data = Shopify.extract_file()
#     Sapo = Sapo_Extractor(bucket)
#     Sapo_data = Sapo.extract_file()

#     print(Shopify_data.info())
#     print(Sapo_data.info())

#     dim_table = Dim_Transformer()
#     da = dim_table.transform_dim_customer(Shopify_data)
#     db = dim_table.transform_dim_product(Shopify_data)
#     dc = dim_table.transform_dim_location(Sapo_data)
#     dd = dim_table.transform_dim_staff(Sapo_data)

#     print(da.head(10))
#     print(da.info())
#     print(db.head(10))
#     print(db.info())
#     print(dc.head(10))
#     print(dc.info())
#     print(dd.head(10))
#     print(dd.info())


