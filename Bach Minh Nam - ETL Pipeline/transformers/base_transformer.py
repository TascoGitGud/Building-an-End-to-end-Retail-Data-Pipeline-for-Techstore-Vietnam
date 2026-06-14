import pandas as pd
import sys
import os
import io

#import logger from utils
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
from utils.logger import setup_logger

class Base_Transformer:
    """
    Base class for data transformation operations.
    Provides common utility methods for date conversion, key generation, 
    and list unflattening using Pandas.
    """
    
    def __init__(self):
        self.logger = setup_logger(__name__)

    def to_date(self, df, columns: list):
        """
        Converts specified columns in a DataFrame to datetime objects.
        Errors during conversion are coerced to NaT (Not a Time).

        Args:
            df (pd.DataFrame): The input DataFrame.
            columns (list): A list of column names to convert.
        """
        try:
            for i in columns:
                if i in df.columns:
                    df[i] = pd.to_datetime(df[i], errors='coerce')
                else:
                    self.logger.warning(f"Column '{i}' not found in DataFrame.")
            return df
       
        except Exception as e:
            self.logger.error(f"Error in to_date transformation: {e}")
            raise e
        
    def convert_ns_to_us(self, df, date_formatted_column):
        """
        
        """
        try: 
            if date_formatted_column in df.columns:
                df[date_formatted_column] = df[date_formatted_column].astype('datetime64[us]')
            else:
                self.logger.warning(f"Column '{date_formatted_column}' not found for US conversion.")
            
            return df
        except Exception as e:
            self.logger.error(f"Error in convert_ns_to_us transformation: {e}")
            raise e
    
    def create_date_key(self, df, date_column, key_date = 'xxx_key_date'): 
        """
        Creates a new date-only key column from a specific datetime column.

        Args:
            df (pd.DataFrame): The input DataFrame.
            date_column (str): The name of the source datetime column.
            key_date (str): The name of the new key column to create. Defaults to 'xxx_key_date'.
        """
        
        try:
            if date_column in df.columns:
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce') #eunsure the input column is in datetime format

                df[key_date] = df[date_column].dt.strftime('%Y%m%d').astype(int)
                
                self.logger.debug(f"Created date key '{key_date}' from '{date_column}'.")
            else:
                self.logger.warning(f"Source column '{date_column}' not found. Cannot create date key.")
            return df
        
        except Exception as e:
            self.logger.error(f"Error in create_date_key: {e}")
            raise e

    def create_surrogate_key(self, df, selected_cols: list, new_key_name = "new_key_name"):
        """
        Creates a surrogate key (composite key) by concatenating values from multiple columns.
        Values are separated by an underscore ('_').

        Args:
            df (pd.DataFrame): The input DataFrame.
            selected_cols (list): List of column names to combine.
            new_key_name (str): The name of the new surrogate key column. Defaults to 'new_key_name'.
        """
  
        try:

            missing_cols = [c for c in selected_cols if c not in df.columns] #check whether selected columns are available in DataFrame
            if missing_cols:
                self.logger.error(f"Columns {missing_cols} not found in DataFrame. Cannot create surrogate key.")
                return df
        
        #combined columns
            separator = "_"
            combined_col = df[selected_cols[0]].astype(str) #pick the first col and convert to string

            for c in selected_cols[1:]:
                combined_col = combined_col + separator + df[c].astype(str)

            df[new_key_name] = combined_col
            self.logger.info(f"Successfully created surrogate key '{new_key_name}'")
            return df

        except Exception as e:
            self.logger.error(f"Error in create_surrogate_key: {e}")
            raise e
        
    def create_order_key(self, df, source_col, order_id_col, new_key_name="order_key"):
        """
        Creates a unique order key by combining the source and the order ID.
        
        Args:
            df (pd.DataFrame): The input DataFrame.
            source_col (str): The column containing the source name.
            order_id_col (str): The column containing the order identifier.
            new_key_name (str): The name of the new column to create.
        """
        try:
            if source_col in df.columns and order_id_col in df.columns:
                df[new_key_name] = df[source_col].astype(str) + "_" + df[order_id_col].astype(str)
                self.logger.info(f"Successfully created order key '{new_key_name}'")
            else:
                self.logger.warning(f"Columns '{source_col}' or '{order_id_col}' not found. Cannot create order key.")
            return df
        except Exception as e:
            self.logger.error(f"Error in create_order_key: {e}")
            raise e

    def unflatten_list(self, df, list_col, col_to_keep):
        """
        Explodes (unflattens) a column containing lists of dictionaries into separate rows.

        Args:
            df (pd.DataFrame): The input DataFrame.
            list_col (str): The column name containing the list of data to unflatten.
            col_to_keep (list): List of other columns to retain (repeat) for each unflattened row.
        """
        try:

            df_dict_version = df.to_dict(orient='records') # Convert DataFrame to a list of dicts for processing
            
            # Normalize JSON data into a flat table
            df_items = pd.json_normalize(
                df_dict_version,
                record_path= list_col,
                meta=col_to_keep,
                errors='ignore'            
                )
            self.logger.info(f"Unflattening complete. Output shape: {df_items.shape}")
            return df_items

        except Exception as e:
            self.logger.error(f"Error in unflatten_list for column '{list_col}': {e}")
            raise e
        
    def data_quality_check(self, df, table_name: str, 
                           critical_null_columns: list = None,
                           key_columns: list = None,
                           date_columns: list = None, 
                           amount_columns: list = None, 
                           allow_negative_amounts: bool = False):
        """
        Performs a comprehensive data quality check and logs the results.
        Flags duplicate rows using a soft delete approach (is_deleted = 1).

        Metrics reported:
        - Total dimensions (Rows/Columns).
        - Count of NULL values per column.
        - Count of duplicate rows.
        - Date Range Validation (if date_columns provided).
        - Amount Validation (if amount_columns provided).

        Args:
            df (pd.DataFrame): The DataFrame to inspect.
            table_name (str): The name of the table (used for logging identification).
            critical_null_columns (list, optional): List of columns that cannot have NULL values.
            key_columns (list, optional): List of columns that form the primary key.
            date_columns (list, optional): List of date columns to validate.
            amount_columns (list, optional): List of amount columns to validate.
            allow_negative_amounts (bool): If True, negative amounts are allowed (e.g., bank transactions).
        """
        try:
            self.logger.info(f"--- Data Quality check: {table_name} ---")

            # Check datatype     
            buffer = io.StringIO()
            df.info(buf=buffer)
            self.logger.info(f"DataFrame Info:\n{buffer.getvalue()}")

            # Null Value Checks
            self.logger.info("--- Null Value Checks ---")
            null_counts = df.isnull().sum()
            
            check_critical_cols = list(critical_null_columns) if critical_null_columns else []
            # Add amount columns if provided 
            if amount_columns:
                for col in amount_columns:
                    if col not in check_critical_cols:
                        check_critical_cols.append(col)
            
            if check_critical_cols:
                for col in check_critical_cols:
                    if col in df.columns:
                        crit_null_count = df[col].isnull().sum()
                        if crit_null_count > 0:
                            self.logger.warning(f"CRITICAL NULL WARNING: Column '{col}' has {crit_null_count} NULL values!")
                    else:
                        self.logger.warning(f"Critical column '{col}' not found in DataFrame for NULL validation.")
            
            cols_with_nulls = null_counts[null_counts > 0]
            if not cols_with_nulls.empty:
                self.logger.warning(f"Found NULL values in columns:\n{cols_with_nulls}")
            else:
                self.logger.info("No NULL values found.")

            # Duplicate Checks (soft delete)
            self.logger.info("--- Duplicate Checks ---")
            df['is_deleted'] = 0
            
            if key_columns:
                # Filter out key columns that exist in the df
                valid_keys = [col for col in key_columns if col in df.columns]
                
                if valid_keys:
                    # Identify duplicate rows based on specific key columns 
                    is_dup = df.duplicated(subset=valid_keys, keep='first')
                    
                    # Flag duplicate is_deleted = 1
                    df.loc[is_dup, 'is_deleted'] = 1
                    
                    duplicate_count = is_dup.sum()
                    if duplicate_count > 0:
                        self.logger.warning(f"Found {duplicate_count} duplicate rows based on keys {valid_keys}! Flagged as is_deleted = 1.")
                    else:
                        self.logger.info(f"No duplicate records found based on keys {valid_keys}.")
                else:
                    self.logger.warning(f"None of the provided key columns {key_columns} found for duplicate check.")
            else:
                # flag is_deleted = 1 for complete row duplicates
                is_dup_all = df.duplicated(keep='first')
                df.loc[is_dup_all, 'is_deleted'] = 1
                all_cols_dup = is_dup_all.sum()
                if all_cols_dup > 0:
                    self.logger.warning(f"Found {all_cols_dup} complete row duplicates! Flagged as is_deleted = 1.")
                
            # Date Range Validation
            if date_columns:
                self.logger.info("--- Date Range Validation ---")
                current_date = pd.Timestamp.now()
                
                for col in date_columns:
                    if col not in df.columns:
                        self.logger.warning(f"Date column '{col}' not found in DataFrame")
                        continue
                    
                    # Remove NaT values
                    valid_dates = df[col].dropna()
                    
                    if len(valid_dates) == 0:
                        self.logger.warning(f"Column '{col}' has no valid dates")
                        continue
                    
                    # Check min/max date range
                    min_date = valid_dates.min()
                    max_date = valid_dates.max()
                    self.logger.info(f"Column '{col}' - Date Range: {min_date} to {max_date}")
                    
                    
                    unreasonable_old = valid_dates[valid_dates < pd.Timestamp('2000-01-01')]
                    unreasonable_future = valid_dates[valid_dates > current_date]
                    
                    if len(unreasonable_old) > 0:
                        self.logger.warning(f"Column '{col}' has {len(unreasonable_old)} dates before 2000")
                    
                    if len(unreasonable_future) > 0:
                        self.logger.warning(f"Column '{col}' has {len(unreasonable_future)} dates after current date")
                    
                    #warning and logs
                    future_dates = valid_dates[valid_dates > current_date]
                    if len(future_dates) > 0:
                        self.logger.warning(f"Column '{col}' has {len(future_dates)} future dates (after {current_date.date()})")
            
            # Amount Validation
            if amount_columns:
                self.logger.info("--- Amount Validation ---")
                
                for col in amount_columns:
                    if col not in df.columns:
                        self.logger.warning(f"Amount column '{col}' not found in DataFrame")
                        continue
                    
                    # Remove NaN values
                    valid_amounts = df[col].dropna()
                    
                    if len(valid_amounts) == 0:
                        self.logger.warning(f"Column '{col}' has no valid amounts")
                        continue
                    
                    # Check for negative amounts
                    negative_count = (valid_amounts < 0).sum()
                    if negative_count > 0:
                        if allow_negative_amounts:
                            self.logger.info(f"Column '{col}' has {negative_count} negative amounts (allowed for this table)")
                        else:
                            self.logger.warning(f"Column '{col}' has {negative_count} negative amounts!")
                    
                    # Statistical summary
                    mean_val = valid_amounts.mean()
                    median_val = valid_amounts.median()
                    std_val = valid_amounts.std()
                    
                    self.logger.info(f"Column '{col}' - Statistical Summary:")
                    self.logger.info(f"  Mean: {mean_val:.2f}")
                    self.logger.info(f"  Median: {median_val:.2f}")
                    self.logger.info(f"  Std Dev: {std_val:.2f}")
                    self.logger.info(f"  Min: {valid_amounts.min():.2f}")
                    self.logger.info(f"  Max: {valid_amounts.max():.2f}")
                    
                    # Identify outliers using IQR method
                    Q1 = valid_amounts.quantile(0.25)
                    Q3 = valid_amounts.quantile(0.75)
                    IQR = Q3 - Q1
                    
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers = valid_amounts[(valid_amounts < lower_bound) | (valid_amounts > upper_bound)]
                    
                    if len(outliers) > 0:
                        self.logger.warning(f"Column '{col}' has {len(outliers)} outliers (using IQR method)")
                        self.logger.warning(f"  Outlier range: < {lower_bound:.2f} or > {upper_bound:.2f}")
                        self.logger.warning(f"  Sample outliers: {outliers.head(5).tolist()}")
                    else:
                        self.logger.info(f"Column '{col}' has no significant outliers")

            return df

        except Exception as e:
            self.logger.error(f"Error in data_quality_check: {e}")
            raise e

    def handle_missing_value(self, df, fill_cols: dict = {}):
        """
        Handles missing values based on defined strategies:
        - FILL: Imputes nulls with default values for other columns.

        Args:
            df (pd.DataFrame): The input DataFrame.
            fill_cols (dict): Dictionary mapping columns to fill values (e.g., {'customer_id': -1}).
        """
        self.logger.info(f"Handling missing values...")
        try:
            if fill_cols:
                for col, value in fill_cols.items():
                    if col in df.columns:
                        missing_count = df[col].isnull().sum()

                        if missing_count > 0:
                            df[col] = df[col].fillna(value)
                            self.logger.info(f"Column {col} HAS FILLED {missing_count} values by '{value}'")
                        else:
                            self.logger.info(f"Column {col} has NO NULL to fill")
                    
                    else:
                        self.logger.info(f"Column {col} not found in DataFrame")
                
            return df
        
        except Exception as e:
            self.logger.error(f"Error in handle_missing_values: {e}")
            raise e