import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractors.sapo_extractor import Sapo_Extractor
from extractors.shopify_extractor import Shopify_Extractor
from extractors.payment_extractor import Payment_Extractor
from extractors.tracking_extractor import Tracking_Extractor
from extractors.online_extractor import Online_Extractor

def test_extraction():
    bucket_name = "minpy"
    print("\nTESTING EXTRACTION SUITE")

    # Test simple extractors
    extractors = [
        ("Sapo", Sapo_Extractor),
        ("Shopify", Shopify_Extractor),
        ("Online", Online_Extractor),     
        ("Tracking", Tracking_Extractor)
    ]

    for name, extractor_class in extractors:
        print(f"\nRUNNING {name} EXTRACTOR")
        try:
            extractor = extractor_class(bucket_name)
            df = extractor.extract_file() 
            print(f"-> {name} Data Shape: {df.shape}")
        except Exception as e:
            print(f"-> ERROR in {name}: {e}")

    # 2. Test Payment Extractor 
    print("\nRUNNING PAYMENT EXTRACTOR")
    try:
        payment = Payment_Extractor(bucket_name)
        payment_methods = {
            "MoMo": payment.payment_momo_extract,
            "ZaloPay": payment.payment_zalopay_extract,
            "PayPal": payment.payment_paypal_extract,
            "Mercury": payment.payment_mercury_extract
        }
        
        for method_name, method_func in payment_methods.items():
            try:
                result = method_func()
                
                # Df or Dict
                if isinstance(result, pd.DataFrame):
                    print(f"-> {method_name} Data Shape: {result.shape}")
                elif isinstance(result, dict):
                    print(f"-> {method_name} returned dictionary containing:")
                    for key, df in result.items():
                        print(f" {key} shape: {df.shape}")
            
            except Exception as e:
                print(f"-> ERROR in {method_name}: {e}")
            
    except Exception as e:
        print(f"-> ERROR in Payment Module: {e}")

    print("\nTESTED SUCCESSFULLY")

if __name__ == "__main__":
    test_extraction()