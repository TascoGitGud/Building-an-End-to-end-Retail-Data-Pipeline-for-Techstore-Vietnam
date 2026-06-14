# test base_transformer 
if __name__ == '__main__':
    import os
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) 
    sys.path.append(project_root)

    from extractors.payment_extractor import Payment_Extractor
    from extractors.shopify_extractor import Shopify_Extractor
    from extractors.online_extractor import Online_Extractor
    from extractors.tracking_extractor import Tracking_Extractor
    from utils.logger import setup_logger
    from transformers.base_transformer import Base_Transformer

    #import data test: payment_momo
    momo = Payment_Extractor('your-bucket-name')
    momo_data = momo.payment_momo_extract()
    momo_data.info()
    
    #import data test: shopify
    shopify= Shopify_Extractor('your-bucket-name')
    shopify_data = shopify.extract_file()


    #test create date_key
    transformer = Base_Transformer()
    momo_data_transform = transformer.to_date(momo_data, ['responseTimeISO'])
    momo_data_transform = transformer.create_date_key(momo_data, 'responseTimeISO', key_date= "payment_date_key")
   
   #test create_order_key
    shopify_data_transform = transformer.create_order_key(shopify_data, 'source', 'order_number')
    shopify_data_transform.head()

    #test unflatten list
    shopify_line_items = transformer.unflatten_list(shopify_data, 'line_items',col_to_keep=['order_number', 'source', 'created_at'])
    shopify_line_items.head()


#test dim_transformer
if __name__ == '__main__':
    import os
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) 
    sys.path.append(project_root)

    from extractors.shopify_extractor import Shopify_Extractor
    from extractors.payment_extractor import Payment_Extractor
    from extractors.online_extractor import Online_Extractor
    from extractors.tracking_extractor import Tracking_Extractor
    
    from transformers.dimension_transformer import Dim_Transformer

    bucket = 'your-bucket-name'

    #test dim_product
    product = Shopify_Extractor(bucket)
    product_data = product.extract_file()

    print(product_data.info())

    dim_table = Dim_Transformer()
    dim_product = dim_table.transform_dim_product(product_data)

    print(dim_product.head(20))
    print(dim_product.info())

    #test dim_customer
    
    customer = Shopify_Extractor(bucket)
    customer_data = customer.extract_file()

    print(customer_data.info())

    dim_table = Dim_Transformer()
    dim_customer = dim_table.transform_dim_customer(customer_data)

    print(dim_customer.head(20))
    print(dim_customer.info())

#test fact_transformers
if __name__ == '__main__':
    import os
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir) 
    sys.path.append(project_root)

    from extractors.shopify_extractor import Shopify_Extractor
    from extractors.payment_extractor import Payment_Extractor
    from extractors.online_extractor import Online_Extractor
    from extractors.tracking_extractor import Tracking_Extractor    
    from utils.logger import setup_logger
    
    from transformers.fact_transformer import Fact_Transformer

    bucket = 'your-bucket-name' # Replace with your actual bucket name
    fact_table = Fact_Transformer()

    #test fact_order_shopify
    shopify = Shopify_Extractor(bucket)
    shopify_data = shopify.extract_file()

    fact_order_shopify = fact_table.fact_order_shopify(shopify_data)
    
    #test fact_order_online
    online_orders = Online_Extractor(bucket)
    online_orders_data = online_orders.extract_file()

    fact_order_online = fact_table.fact_order_online(online_orders_data)
    
    #test union
    fact_order = fact_table.create_fact_order(fact_order_shopify, fact_order_online)

    print(fact_order.head())
    print(fact_order.info())


    momo_data = Payment_Extractor('your-bucket-name').payment_momo_extract()
    zalopay_data = Payment_Extractor('your-bucket-name').payment_zalopay_extract()
    paypal_data = Payment_Extractor('your-bucket-name').payment_paypal_extract()

    fact_payment_momo = fact_table.fact_payment_momo(momo_data)
    fact_payment_zalopay = fact_table.fact_payment_zalopay(zalopay_data)
    fact_payment_paypal = fact_table.fact_payment_paypal(paypal_data)

    fact_payment = fact_table.create_fact_payment(fact_payment_zalopay, fact_payment_momo, fact_payment_paypal)

    print(fact_payment.head(10))

    print(fact_payment.info())

    #fact_order_items
    shopify = Shopify_Extractor(bucket)
    shopify_data = shopify.extract_file()

    fact_order_shopify = fact_table.fact_order_shopify(shopify_data)

    fact_order_items_shopify = fact_table.fact_order_items_shopify(fact_order_shopify, shopify_data)


    online = Online_Extractor(bucket)
    online_data = online.extract_file()

    fact_order_online = fact_table.fact_order_online(online_data)

    fact_order_items_online = fact_table.fact_order_items_online(fact_order_online, online_data)

    fact_order_items = fact_table.create_fact_order_items(fact_order_items_shopify, fact_order_items_shopify)

    fact_order_items.info()

    cart_events = Tracking_Extractor(bucket)
    cart_events_data = cart_events.extract_file()

    fact_cart_events = fact_table.creat_fact_cart_events(cart_events_data)

    print(fact_cart_events.head(10))

