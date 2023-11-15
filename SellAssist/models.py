import requests
from django.db import models
from django.core.exceptions import ValidationError
from Octopus.models import GlobalSettings
import datetime
import json
import re
# Create your models here.


class SellAssistAPI(models.Model):
    endpoint = models.CharField(max_length=200)
    apikey = models.CharField(max_length=200)

    def clean(self):
        apis = SellAssistAPI.objects.all()

        if not len(apis)<=1:
            raise ValidationError('There is not place for more API keys')
        elif len(apis) == 1:
            api = apis[0]
            if self.id != api.id:
                raise ValidationError('There is not place for more API keys')


    def callapi(self, uri, body, method):
        try:
            endpoint = self.endpoint
            apikey = self.apikey
            url = (endpoint + uri) if len(uri) > 0 else endpoint
            headers = {}
            headers['accept'] = 'application/json'
            headers['apiKey'] = apikey

            for element in headers:
                if headers[element] is None:
                    raise ValueError

            response = None
            if method == 'GET':
                response = requests.get(headers=headers, url=url)
            elif method == 'POST':
                headers['Content-Type'] = 'application/json'
                response = requests.post(headers=headers, url=url, data=body)

            if response.status_code == 200:
                return json.loads(response.text)
            else:
                raise requests.exceptions.RequestException('Wrong response code!')

        except ValueError as Error:
            print(1)
        except Exception as Error:
            print(Error)

    def getproductdata(self, product_id):
        method = 'GET'
        uri = f'/products/{product_id}'
        body = ''
        response = self.callapi(uri, body, method)
        return response

    def getproductlist(self):
        method = 'GET'
        uri = '/products/'
        body = ''
        response = self.callapi(uri,body,method)
        return response

    def registerproducts(self):
        products = self.getproductlist()
        if products is not None:
            if isinstance(products,list):
                if len(products) > 0:
                    for product in products:
                        variants = product.get('variants')
                        if variants is not None and len(variants)>0:
                            self.registervariants(product)
                        else:
                            self.registersimple(product)

    def registervariants(self, product):
        variants = product.get('variants')
        for variant in variants:
            ean = variant.get('ean')
            if re.match(r'^\d{1,20}$', str(ean)):
                try:
                    SellAssistProduct.objects.get(ean=ean)
                except SellAssistProduct.DoesNotExist:
                    newproduct = SellAssistProduct()
                    newproduct.ean = ean
                    newproduct.variant_id = variant.get('id')
                    newproduct.name = f'{product.get("name")}-{variant.get("id")}'
                    newproduct.product_id = product.get('id')
                    newproduct.sku = variant.get('catalog_number')
                    newproduct.clean()
                    newproduct.save()

    def registersimple(self,product):
        ean = product.get('ean')
        if re.match(r'^\d{1,20}$', str(ean)):
            try:
                SellAssistProduct.objects.get(ean=ean)
            except SellAssistProduct.DoesNotExist:
                newproduct = SellAssistProduct()
                newproduct.ean = ean
                newproduct.name = product.get('name') if product.get('name') not in ['',None] else product.get('id')
                newproduct.product_id = product.get('id')
                newproduct.sku = product.get('catalog_number')
                newproduct.clean()
                newproduct.save()


class SellAssistPickupPoint(models.Model):
    code = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    address = models.CharField(max_length=200)

    def return_json(self) -> dict:
        obj_json = {}
        obj_json['code'] = self.code
        obj_json['type'] = self.type
        obj_json['address'] = self.address
        return obj_json

    def return_empty(self) -> dict:
        obj_json = {}
        obj_json['code'] = ''
        obj_json['type'] = ''
        obj_json['address'] = ''
        return obj_json


class SellAssistPayment(models.Model):
    default = models.BooleanField(default=False)
    payment_id = models.IntegerField(null=True)
    title = models.CharField(max_length=200)

    def clean(self):
        if not len(SellAssistPayment.objects.filter(default=True)) == 0:
            raise ValidationError('Cannot be more than one default payment method')


class SellAssistShipment(models.Model):
    default = models.BooleanField(default=False)
    shipment_id = models.IntegerField(null=True)
    title = models.CharField(max_length=200)

    def clean(self):
        if not len(SellAssistShipment.objects.filter(default=True)) == 0:
            raise ValidationError('Cannot be more than one default shipment method')


class SellAssistProduct(models.Model):
    product_id = models.CharField(max_length=200)
    variant_id = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    ean = models.CharField(max_length=20)
    sku = models.CharField(max_length=20)
    is_bundle = models.BooleanField(default=False)
    bundle_id = models.IntegerField(default=0)
    quantity = models.FloatField(default=0)




class SellAssistRegisteredProduct(SellAssistProduct):
    pass

    def clean(self):
        try:
            newproduct = SellAssistRegisteredProduct.objects.get(ean=self.ean)
            if self.id != newproduct.id:
                raise ValidationError('EAN duplication')
        except SellAssistRegisteredProduct.DoesNotExist:
            pass


class SellAssistUnknownProduct(SellAssistProduct):
    product_id = '0'
    variant_id = '0'
    is_bundle = None
    bundle_id = None
    quantity = None
    def clean(self):
        pass


class SellAssistCountry(models.Model):
    code = models.CharField(max_length=3)

    def return_json(self) -> dict:
        obj_json = {}
        obj_json['id'] = ''
        obj_json['name'] = ''
        obj_json['code'] = self.code
        return obj_json

    def return_empty_json(self) -> dict:
        obj_json = {}
        obj_json['id'] = 0
        obj_json['name'] = ''
        obj_json['code'] = ''
        return obj_json


class SellAssistAddress(models.Model):
    name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    street = models.CharField(max_length=200)
    home_number = models.CharField(max_length=200)
    flat_number = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    postcode = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    phone = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    company_nip = models.CharField(max_length=200)
    country = models.ForeignKey(SellAssistCountry, on_delete=models.SET_NULL, null=True)

    def return_json(self) -> dict:
        obj_json = {}
        obj_json['name'] = self.name
        obj_json['surname'] = self.surname
        obj_json['street'] = self.street
        obj_json['home_number'] = self.home_number
        obj_json['flat_number'] = self.flat_number
        obj_json['description'] = self.description
        obj_json['postcode'] = self.postcode
        obj_json['city'] = self.city
        obj_json['state'] = self.state
        obj_json['phone'] = self.phone
        obj_json['company_name'] = self.company_name
        obj_json['company_nip'] = self.company_nip
        obj_json['country'] = self.country.return_json()
        return obj_json


class SellAssistOrder(models.Model):
    payment_statues = (
        ('paid','paid'),
        ('unpaid','unpaid'),
        ('partial','partial'),
        ('excess','excess'),
        ('unknown','unknown'),
    )

    create = models.DateField(null=True)
    currency_code = models.CharField(max_length=3)
    payment_status = models.CharField(max_length=10, choices=payment_statues,default='unknown')
    status = models.IntegerField()
    date = models.CharField(max_length=200)
    shipment_price = models.FloatField()
    deadline = models.DateField()
    important = models.BooleanField(default=False)
    payment = models.ForeignKey(SellAssistPayment,on_delete=models.SET_NULL, null=True)
    shipment = models.ForeignKey(SellAssistShipment, on_delete=models.SET_NULL,null=True)
    invoice = models.BooleanField(default=False)
    document_number = models.CharField(max_length=200)
    comment = models.CharField(max_length=200)
    bill_address = models.ForeignKey(SellAssistAddress,on_delete=models.SET_NULL,null=True,related_name='bill_address')
    shipment_address = models.ForeignKey(SellAssistAddress,on_delete=models.SET_NULL,null=True,related_name='shipment_address')
    marketplace_id = models.CharField(max_length=200,null=True)
    sellassist_id = models.CharField(max_length=200, null=True)
    registered = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    shipped = models.BooleanField(default=False)
    has_errors = models.BooleanField(default=False)
    validated = models.BooleanField(default=False)
    messages = models.TextField(null=True,blank=True,default=None)
    tracking_num = models.CharField(max_length=200,default='')
    marketplace = models.CharField(max_length=200)

    def return_json(self) -> dict:
        try:
            delivery_time = int(GlobalSettings.objects.get(name='default_delivery_time'))
        except GlobalSettings.DoesNotExist:
            delivery_time = 2
        except ValueError:
            delivery_time = 2

        try:
            default_payment_id = GlobalSettings.objects.get(name='default_payment')
        except GlobalSettings.DoesNotExist:
            default_payment_id = None

        try:
            default_payment = None
            if default_payment_id is not None:
                default_payment = SellAssistPayment.objects.get(payment_id=default_payment_id)
        except SellAssistPayment.DoesNotExist:
            default_payment = None

        try:
            default_shipment_id = GlobalSettings.objects.get(name ='default_shipment')
        except GlobalSettings.DoesNotExist:
            default_shipment_id = None

        try:
            default_shipment = None
            if default_shipment_id is not None:
                default_shipment = SellAssistShipment.objects.get(shipment_id=default_shipment_id)
        except SellAssistShipment.DoesNotExist:
            default_shipment = None

        deadline = self.deadline - datetime.timedelta(days=delivery_time)
        obj_json = {}

        obj_json['currency'] = self.currency_code
        obj_json['create'] = self.create.strftime('%Y-%m-%d %H:%M')
        obj_json['date'] = {self.create.strftime('%Y-%m-%d %H:%M')}
        obj_json['id'] = self.marketplace_id
        obj_json['payment_status'] = self.payment_status if self.payment_statues != 'unknown' else 'unpaid'
        obj_json['status'] = self.status
        obj_json['date'] = self.date
        obj_json['shipment_price'] = self.shipment_price
        obj_json['deadline'] = deadline.strftime('%Y-%m-%d') if deadline is not None else ''
        obj_json['important'] = self.important
        obj_json['invoice'] = 1 if self.invoice else 0
        obj_json['document_number'] = self.document_number
        obj_json['bill_address'] = self.bill_address.return_json()
        obj_json['shipment_address'] = self.shipment_address.return_json()

        if self.payment is not None:
            obj_json['payment_id'] = self.payment.payment_id
            obj_json['payment_name'] = self.payment.title
        elif default_payment is not None:
            obj_json['payment_id'] = default_payment.payment_id
            obj_json['payment_name'] = default_payment.title
        else:
            obj_json['payment_id'] = 0
            obj_json['payment_name'] = 'Unknown'

        if self.shipment is not None:
            obj_json['shipment_id'] = self.shipment.shipment_id
            obj_json['shipment_name'] = self.shipment.title
        elif default_shipment is not None:
            obj_json['shipment_id'] = default_shipment.shipment_id
            obj_json['shipment_name'] = default_shipment.title
        else:
            obj_json['shipment_id'] = 0
            obj_json['shipment_name'] = 'Unknown'


        carts = SellAssistCart.objects.filter(order=self)
        if len(carts)>0:
            obj_json['carts'] = []
            for index, cart in enumerate(carts):
                json_cart = cart.return_json()
                json_cart['id'] = index
                obj_json['carts'].append(json_cart)
        return obj_json



    def clean(self):
        self.validateorder()

    def validateorder(self):
        status = True
        elements = [self.bill_address,self.shipment_address,self.marketplace_id]
        if None in elements:
            status = False
        if self.payment_status == 'unknown':
            status = False

        if self.has_errors:
            status = False

        if len(SellAssistCart.objects.filter(order=self)) == 0:
            status = False

        if self.payment is None:
            try:
                SellAssistPayment.objects.get(default=True)
            except SellAssistPayment.DoesNotExist:
                status = False

        if self.shipment is None:
            try:
                SellAssistShipment.objects.get(default=True)
            except SellAssistShipment.DoesNotExist:
                status = False

        self.validated = status
        self.save()


    def registerorder(self):
        uri = '/orders/'
        method = 'POST'
        json_data = json.dumps(self.return_json())
        api = SellAssistAPI.objects.first()

        if not self.validated:
            self.validateorder()

        if self.validated:
            try:
                response = api.callapi(uri=uri, method=method,body=json_data)
                print(response)
                sellassistid = response.get('id')
                if sellassistid is not None:
                    self.sellassist_id = sellassistid
                    self.registered = True

            except requests.exceptions.RequestException as Error:
                self.has_errors = True
                self.messages = Error

        self.clean()
        self.save()



class SellAssistCart(models.Model):
    order = models.ForeignKey(SellAssistOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(SellAssistProduct, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    price = models.FloatField()
    stock_update = models.BooleanField(default=True)
    additional_information = models.CharField(max_length=200)

    def __str__(self):
        return f'{self.id}: {self.product_id}'


    def return_json(self) -> dict:
        obj_json = {}
        obj_json['product_id'] = self.product.product_id
        obj_json['variant_id'] = self.product.variant_id
        obj_json['name'] = self.product.name
        obj_json['catalog_number'] = self.product.ean
        obj_json['price'] = self.price
        obj_json['quantity'] = self.quantity
        obj_json['stock_update'] = 1 if self.stock_update else 0
        return obj_json


