from google.cloud import storage
import pandas as pd
from extractors.base_extractor import Base_Extractor

class Payment_Extractor(Base_Extractor):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)

    def payment_mercury_extract(self):

        "Create extract function for payment gateway: mercury"

        blob_path = r'mercury/'
        list_files_extract = self.list_files(blob_path)
        print(f"Found files: {list_files_extract}")

        data_extract = {} # Dict due to there are 2 different data structure
        for i in list_files_extract:

            data = self.extract_json_gz(i)
            df = pd.DataFrame(data) 

            clean_key = i.split('/')[-1].replace('.json.gz','') 
            data_extract[clean_key] = df 

        return data_extract
    
    def payment_momo_extract(self):
        "Create extract function for payment gateway: momo"
        blob_path = r'momo/'
        list_files_extract = self.list_files(blob_path)
        print(f"Found files: {list_files_extract}")

        data_extract = []
        for i in list_files_extract:
            data = self.extract_json_gz(i)
            if isinstance(data, list):
                data_extract.extend(data)
            elif isinstance(data, dict):
                data_extract.extend(data.get('id', [data]))
        
        df = pd.DataFrame(data_extract)
        return df
    
    def payment_paypal_extract(self):
        "Create extract function for payment gateway: paypal"
        blob_path = r'paypal/'
        list_files_extract = self.list_files(blob_path)
        print(f"Found files: {list_files_extract}")

        data_extract = []
        for i in list_files_extract:
            data = self.extract_json_gz(i)
            if isinstance(data, list):
                data_extract.extend(data)
            elif isinstance(data, dict):
                data_extract.extend(data.get('id', [data]))
        
        df = pd.DataFrame(data_extract)
        return df
    
    def payment_zalopay_extract(self):
        "Create extract function for payment gateway: zalopay"
        blob_path = r'zalopay/'
        list_files_extract = self.list_files(blob_path)
        print(f"Found files: {list_files_extract}")

        data_extract = []
        for i in list_files_extract:
            data = self.extract_json_gz(i)
            if isinstance(data, list):
                data_extract.extend(data)
            elif isinstance(data, dict):
                data_extract.extend(data.get('id', [data]))
        
        df = pd.DataFrame(data_extract)
        return df

