import logging
import os
from datetime import datetime

def setup_logger(module_name: str, log_folder: str = 'logs', log_filename: str = 'pipeline.log') -> logging.Logger:
    """
    Sets up and returns a centralized logger instance.
    This logger will write to both the console (terminal) and a file.
    """
    
    # Create log folder if it doesn't exist
    if not os.path.exists(log_folder):
        try:
            os.makedirs(log_folder)
        except OSError as e:
            print(f"Error creating log directory: {e}")

    # Define the Log Format
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Get the logger instance
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)

    # Check if handlers already exist to avoid duplicate logs
    if not logger.handlers:
        
        # Write to File
        file_path = os.path.join(log_folder, log_filename)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)

        # Print to Console
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(log_format)
        logger.addHandler(stream_handler)

    return logger