import sys
import time
from datetime import datetime
from orchestration.pipeline_orchestrator import Pipeline_Orchestrator
from utils.logger import setup_logger


BUCKET_NAME = 'your-bucket-name'  # Replace with your actual bucket name
DATASET_ID = 'name_of_your_dataset'  # Replace with your actual dataset name

def main():
    """
    Main entry point for the ETL Pipeline.
    Measures execution time and handles errors.
    """
    
    logger = setup_logger('main')
    
    logger.info("="*50)
    logger.info(f"ETL PIPELINE STARTED AT: {datetime.now()}")
    logger.info("="*50)

    start_time = time.time()

    try:
        logger.info(f"Initializing Pipeline with Bucket: '{BUCKET_NAME}' | Dataset: '{DATASET_ID}'")
        pipeline = Pipeline_Orchestrator(BUCKET_NAME, DATASET_ID)

        # Run the full ETL pipeline
        pipeline.orchestrator_run() 
        
        # Calculate execution time
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("="*50)
        logger.info(f"ETL PIPELINE FINISHED SUCCESSFULLY")
        logger.info(f"Total Execution Time: {duration:.2f} seconds")
        logger.info("="*50)

    except Exception as e:

        logger.critical("="*50)
        logger.critical(f"ETL PIPELINE FAILED:")
        logger.critical(f"Error Details: {e}")
        logger.critical("="*50)
        
main()