import gzip
from google.cloud import storage
import json
import os
import sys
from utils.logger import setup_logger
from utils.config import load_env_variables, get_gcs_credentials_path

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

class Base_Extractor:
    """
    Base class for all source extractors.
    Handles common functionality such as connecting to GCS, listing files in a bucket, and extracting data from .json.gz files.
    """

    def __init__(self, bucket_name: str):
        """
        Initializes the Base_Extractor with a connection to the specified GCS bucket.
        Args:
            bucket_name (str): The name of the GCS bucket to connect to.
        """
        self.logger = setup_logger(__name__)

        try:
            # Load environment variables
            load_env_variables()
            
            # Set up credentials from environment variable
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = get_gcs_credentials_path()

            # Connect to GCS Bucket
            self.client = storage.Client() 
            self.bucket = self.client.bucket(bucket_name) 

            self.logger.info(f'Successfully connected to GCS')
        except Exception as e:
            self.logger.error(f"Failed to connected to GCS: {e}")
            raise e
        
    def extract_json_gz(self, blob_path: str): 
        """
        Downloads a .json.gz file from GCS, decompresses it, and parses the JSON content.
        
        Args:
            blob_path (str): The path to the .json.gz file in the GCS bucket.
        Returns:
            dict or list: The parsed JSON data from the file, which can be either a dictionary or a list
        """

        try:
            # Identify the blob
            blob = self.bucket.blob(blob_path) 

            # Download files
            compressed_data = blob.download_as_bytes() 

            # Decompress gzip data
            decompressed_data = gzip.decompress(compressed_data) 
            
            # Decode and parse json 
            json_data = json.loads(decompressed_data.decode("utf-8"))
            self.logger.debug(f"Successfully extracted data from {blob_path}")
            return json_data
        
        except Exception as e:
            self.logger.error(f"Failed to extract file {blob_path}: {e}")
            raise e

    def list_files(self, folder_name):
        """
        Lists all files in a specified folder within the GCS bucket.

        Args:
            folder_name (str): The name of the folder within the bucket to list files from.
        Returns:
            list: A list of file paths within the specified folder.
        """
        
        try:
            blobs = self.client.list_blobs(self.bucket, prefix= folder_name) #create a list of blobs
            file_path = []

            for i in blobs:
                if not i.name.endswith('/'): # Filter out folder objects, keep only files
                    file_path.append(i.name)
            return  file_path
        
        except Exception as e:
            self.logger.error(f"Error listing files in folder '{folder_name}': {e}")
            raise e
    
