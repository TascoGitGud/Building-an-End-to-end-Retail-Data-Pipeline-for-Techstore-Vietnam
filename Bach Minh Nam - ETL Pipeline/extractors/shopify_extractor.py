from google.cloud import storage
import pandas as pd
from extractors.base_extractor import Base_Extractor


class Shopify_Extractor(Base_Extractor):
    def __init__(self, bucket_name):
        super().__init__(bucket_name)

    def extract_file(self):
        shopify_blob_path = r'shopify/'
        list_files_extract = self.list_files(shopify_blob_path)
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

