import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors.sapo_extractor import Sapo_Extractor
from extractors.shopify_extractor import Shopify_Extractor
from extractors.payment_extractor import Payment_Extractor
from extractors.tracking_extractor import Tracking_Extractor
from extractors.online_extractor import Online_Extractor

def preview_json(data, limit=1500):
    return json.dumps(data, indent=4, ensure_ascii=False)[:limit]

def inspect_source(name, extractor, folder):
    print(f"\n[INSPECTING] {name}")
    try:
        files = extractor.list_files(folder)
        if not files:
            print(f"[WARNING] No files found in: {folder}")
            return
        
        file_path = files[0]
        data = extractor.extract_json_gz(file_path)
        
        first_record = data[0] if isinstance(data, list) and len(data) > 0 else data
        
        print(f"[SUCCESS] Previewing: {file_path}")
        print(preview_json(first_record))
    except Exception as e:
        print(f"[ERROR] Failed to inspect {name}: {e}")

def Run_Data_Inspector():
    bucket = "minpy"
    
    sources = [
        ("Sapo", Sapo_Extractor(bucket), "sapo/"),
        ("Shopify", Shopify_Extractor(bucket), "shopify/"),
        ("Online", Online_Extractor(bucket), "online_orders/"),
        ("Tracking", Tracking_Extractor(bucket), "cart_tracking/"),
        ("MoMo", Payment_Extractor(bucket), "momo/"),
        ("ZaloPay", Payment_Extractor(bucket), "zalopay/"),
        ("PayPal", Payment_Extractor(bucket), "paypal/"),
        ("Mercury", Payment_Extractor(bucket), "mercury/")
    ]
    
    print("DATA STRUCTURE INSPECTOR")
    
    for name, ext, folder in sources:
        inspect_source(name, ext, folder)
        print("-" * 50)

    print("\n[DONE] Inspection Finished.")

if __name__ == "__main__":
    Run_Data_Inspector()