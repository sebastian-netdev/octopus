from SellAssist.models import SellAssistRegisteredProduct,SellAssistAPI, SellAssistAdditionalFields
from celery import shared_task
import re

@shared_task
def registerproducts():
    api = SellAssistAPI.objects.first()
    products = api.getproductlist()
    if products is not None:
        if isinstance(products, list):
            if len(products) > 0:
                for product in products:
                    product_id = product.get('id')
                    if product_id is not None:
                        product_data = api.getproductdata(product_id)
                        if product_data is not None:
                            variants = product_data.get('variants')
                            if variants is not None and len(variants) > 0:
                                registervariants(product_data)
                            else:
                                registersimple(product_data)
                        
                        
def registervariants(product):
    variants = product.get('variants')
    for variant in variants:
        ean = variant.get('ean')
        if re.match(r'^\d{1,20}$', str(ean)):
            try:
                SellAssistRegisteredProduct.objects.get(ean=ean)
            except SellAssistRegisteredProduct.DoesNotExist:
                newproduct = SellAssistRegisteredProduct()
                newproduct.ean = ean
                newproduct.variant_id = variant.get('id')

                name = product.get("title")
                properties = variant.get('properties')


                for property  in properties:
                    if property.get('name') is not None:
                        name = name + ' ' + property.get('name')


                newproduct.name = name
                newproduct.product_id = product.get('id')
                newproduct.sku = variant.get('catalog') if variant.get('catalog') is not None else ''
                newproduct.clean()
                newproduct.save()

def registersimple(product):
    ean = product.get('ean')
    #print(product)
    if re.match(r'^\d{1,20}$', str(ean)):
        try:
            SellAssistRegisteredProduct.objects.get(ean=ean)
        except SellAssistRegisteredProduct.DoesNotExist:
            newproduct = SellAssistRegisteredProduct()
            newproduct.ean = ean
            newproduct.name = product.get('title') if product.get('title') not in ['',None] else product.get('id')
            newproduct.product_id = product.get('id')
            newproduct.sku = product.get('catalog_number') if product.get('catalog') is not None else ''
            newproduct.clean()
            newproduct.save()


@shared_task
def stockupdate():
    api = SellAssistAPI.objects.first()
    productlist = api.getproductlist()
    for element in productlist:
        product_id = element.get('id')
        product_data = api.getproductdata(product_id)
        variants = product_data.get('variants')
        if variants is not None and len(variants) > 0:
            for variant in variants:
                product_id = product_data.get('id')
                variant_id = variant.get('id')
                try:
                    product = SellAssistRegisteredProduct.objects.get(variant_id=variant_id, product_id=product_id)
                    quantity = variant.get('quantity')
                    if quantity not in [None, '']:
                        if quantity < 0:
                            quantity = 0
                        product.quantity = quantity
                        product.save()

                except SellAssistRegisteredProduct.DoesNotExist:
                    pass
                except SellAssistRegisteredProduct.MultipleObjectsReturned:
                    pass
@shared_task
def getorderfields():
            api = SellAssistAPI.objects.first()
            if api is not None:
                fields = api.getordersfields()
                if fields is not None:
                    for field in fields:
                        try:
                            field_id = field.get('id')
                            field = SellAssistAdditionalFields.objects.get(field_id=field_id)
                        except SellAssistAdditionalFields.DoesNotExist:
                            newfield = SellAssistAdditionalFields()
                            newfield.field_id = field.get('id')
                            newfield.field_type = field.get('type')
                            newfield.name = field.get('name')
                            newfield.save()


