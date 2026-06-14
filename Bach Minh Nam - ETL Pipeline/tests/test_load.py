if __name__ == '__main__':
    import os
    import sys
    import pandas as pd

    # Set up project root directory to handle imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)

    from extractors.shopify_extractor import Shopify_Extractor
    from transformers.dimension_transformer import Dim_Transformer
    from loaders.bigquery_loader import BigQueryLoader

    # Configuration constants
    BUCKET = 'minpy'
    DATASET_ID = 'end_to_end_project'
    
    # Initialize pipeline components
    extractor = Shopify_Extractor(BUCKET)
    dim_transformer = Dim_Transformer()
    loader = BigQueryLoader()

    try:
        print("--- Starting ETL process ---")
        
        # 1. Extract and Transform
        # Extract raw data from GCS and transform into dimension format
        raw_data = extractor.extract_file()
        dim_customer = dim_transformer.transform_dim_customer(raw_data)
        
        # 2. Prepare BigQuery Environment
        # Ensure the target dataset exists
        loader.check_dataset_available(DATASET_ID)

        # 3. Test: Handle empty DataFrame scenario
        print("--- Testing: Load empty DataFrame ---")
        loader.load_dataframe(pd.DataFrame(), DATASET_ID, 'dim_empty')

        # 4. Load processed data into BigQuery
        print(f"--- Loading data into {DATASET_ID}.dim_customer ---")
        loader.load_dataframe(
            dim_customer, 
            DATASET_ID, 
            'dim_customer', 
            write_disposition='WRITE_TRUNCATE'
        )
        
        print("--- ETL process completed successfully! ---")

    except Exception as e:
        print(f"--- An error occurred during execution: {e} ---")