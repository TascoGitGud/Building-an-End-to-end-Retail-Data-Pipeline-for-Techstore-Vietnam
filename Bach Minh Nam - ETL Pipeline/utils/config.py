import os
from dotenv import load_dotenv

def load_env_variables():
    """
    Load environment variables from .env file.
    """
    # Load .env file from project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, '.env')
    
    load_dotenv(env_path)
    
def get_gcs_credentials_path():
    """
    Get the path to GCS service account credentials from environment variable.
    
    Returns:
        str: Path to GCS credentials JSON file
    Raises:
        ValueError: If environment variable is not set
    """
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not creds_path:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
            "Please create a .env file based on .env.example"
        )
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"GCS credentials file not found at: {creds_path}")
    
    return creds_path

def get_bigquery_credentials_path():
    """
    Get the path to BigQuery service account credentials from environment variable.
    
    Returns:
        str: Path to BigQuery credentials JSON file
    Raises:
        ValueError: If environment variable is not set
    """
    creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_BIGQUERY')
    
    if not creds_path:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS_BIGQUERY environment variable not set. "
            "Please create a .env file based on .env.example"
        )
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"BigQuery credentials file not found at: {creds_path}")
    
    return creds_path
