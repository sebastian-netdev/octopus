from django.db import models
from Octopus.models import GlobalSettings,MarketplaceOffer
from SellAssist.models import *
# Create your models here.
import hmac
import hashlib
import time
import requests
import json
import datetime




class KauflandAPICallLog(models.Model):
    timestamp = models.DateField(auto_now=True)
    status_code = models.IntegerField()
    has_error = models.BooleanField(default=False)
    response = models.TextField()
    method = models.CharField(max_length=200)


class KauflandAPI(models.Model):
    periods = (
        ('1h', '1h'),
        ('4h', '4h'),
        ('8h', '8h'),
        ('24', '24h'),
    )

    endpoint = models.CharField(max_length=200)
    clientkey = models.CharField(max_length=200)
    secretkey = models.CharField(max_length=200)
    stock_synchro = models.CharField(max_length=10, choices=periods, default='4h')
    price_synchro = models.CharField(max_length=10, choices=periods, default='4h')

    def signrequest(self, method, uri, body, timestamp, secret_key):
        if body is None:
            body = ''
        try:
            plain_text = "\n".join([method, uri, body, timestamp])
            digest_maker = hmac.new(secret_key.encode(), None, hashlib.sha256)
            digest_maker.update(plain_text.encode())
            hmac_sign = digest_maker.hexdigest()
            return hmac_sign
        except ValueError:
            return None
    def preparegeturl(self,url,params):
        for index, element in enumerate(params):
            if index == 0:
                url = url + '?'
                url = url + element + "=" + params[element]
            else:
                url = url + "&" + element + "=" + params[element]

        return url

    def callapi(self, uri, body, method, return_raw_response=False):
        try:
            timestamp = str(int(time.time()))
            endpoint = self.endpoint
            secretkey = self.secretkey
            url = (endpoint + uri) if len(uri) > 0 else endpoint
            headers = {}
            headers['Accept'] = 'application/json'
            headers['Shop-Client-Key'] = self.clientkey
            headers['Shop-Timestamp'] = timestamp
            headers['User-Agent'] = 'Inhouse_development'
            if method == 'POST':
                headers['Shop-Signature'] = self.signrequest(method, url, body, timestamp, secretkey)
            elif method == 'GET':
                url = self.preparegeturl(url,body)
                headers['Shop-Signature'] = self.signrequest(method, url, '', timestamp, secretkey)

            for element in headers:
                if headers[element] is None:
                    raise ValueError(f'One({element}) or more headers are None')
            response = None
            if method == 'GET':
                response = requests.get(headers=headers, url=url)

            elif method == 'POST':
                headers['Content-Type'] = 'application/json'
                body = json.dumps(body)
                response = requests.post(headers=headers,url=url,data=body)
            if return_raw_response:
                return response
            if response.status_code in [200,201]:
                return json.loads(response.text)
            else:
                print(response.text)
                raise requests.exceptions.RequestException('Wrong response code!')

        except KeyError as Error:
            print(Error)

    def updateoffer(self,body):
        uri = '/units/'
        method = 'POST'
        body = body
        response = self.callapi(uri,body,method)
        return response


    def getoffers(self,body=None,id_offer=None):
        uri = '/units/'
        if id_offer is not None:
            uri = f'/units/{id_offer}'
        method = 'GET'
        response = self.callapi(uri,body,method)
        return response


    def getproduct(self,id_product,storefront):
        method = 'GET'
        body = {}
        body['storefront'] = storefront
        body['id_product'] = str(id_product)
        uri = f'/products/{id_product}'
        response = self.callapi(method=method,uri=uri,body=body)
        return  response

    def getstorefronts(self):
        method = 'GET'
        body = ''
        uri = '/info/storefront'

        response = self.callapi(method=method,uri=uri,body=body)
        return response

    def getorders(self):
        uri = '/orders/'
        method = 'GET'
        body = ''
        response = self.callapi(uri, body, method)
        return response

    def getorderdata(self,order_id):
        uri = f'/orders/{order_id}'
        method = 'GET'
        body = ''
        response = self.callapi(uri,body,method)
        return response

    def convertaddress(self,address):
        newaddress = SellAssistAddress()
        newaddress.name = address.get('first_name') if address.get('first_name') is not None else ''
        newaddress.surname = address.get('last_name') if address.get('last_name') is not None else ''
        newaddress.street = address.get('street') if address.get('street') is not None else ''
        newaddress.home_number = address.get('house_number') if address.get('house_number') is not None else ''
        newaddress.flat_number = ''
        newaddress.description = address.get('additional_field') if address.get('additional_field') is not None else ''
        newaddress.postcode = address.get('postcode') if address.get('postcode') is not None else ''
        newaddress.city = address.get('city') if address.get('city') is not None else ''
        newaddress.state = ''
        newaddress.phone = address.get('phone') if address.get('phone') is not None else ''
        newaddress.company_name = address.get('company_name') if address.get('company_name') is not None else ''
        newaddress.company_nip = ''

        country_code = address.get('country')
        if country_code is not None:
            country_code = country_code.lower()
        else:
            raise ValueError('Country code cannot be None')
        try:
            newaddress.country = SellAssistCountry.objects.get(code=country_code)
        except SellAssistCountry.DoesNotExist:
            country = SellAssistCountry()
            country.code = country_code
            country.save()
            newaddress.country = country
        newaddress.clean()
        newaddress.save()
        return newaddress

    def createorders(self):
        orders = self.getorders()
        for order in orders.get('data'):
            if order is not None:
                external_id = order.get('id_order')
                try:
                    SellAssistOrder.objects.get(marketplace_id=external_id)
                except SellAssistOrder.DoesNotExist:
                    order_data = self.getorderdata(external_id)
                    order_data = order_data.get('data')
                    if order_data is not None:

                        units = order_data.get('order_units')
                        ready_for_shipment = True
                        currency = None
                        if len(units) > 0:
                            shipping_rate = 0
                            delivery_time_min = None
                            for unit in units:
                                if unit.get('status') not in ['need_to_be_sent', 'sent']:
                                    ready_for_shipment = False
                                else:
                                    currency = unit.get('currency')
                                    shipping_rate = shipping_rate + unit.get('shipping_rate')
                                    if delivery_time_min is None:
                                        delivery_time_min = unit.get('delivery_time_min')
                                    else:
                                        if unit.get('delivery_time_min') is not None and unit.get('delivery_time_min') < delivery_time_min:
                                            delivery_time_min = unit.get('delivery_time_min')
                            if ready_for_shipment:
                                neworder = SellAssistOrder()
                                neworder.currency_code = currency
                                neworder.marketplace_id = order_data.get('id_order')
                                kaufland_billing_address = order_data.get('billing_address')
                                kaufland_shipping_address = order_data.get('shipping_address')
                                try:
                                    neworder.bill_address = self.convertaddress(kaufland_billing_address)
                                    neworder.shipment_address = self.convertaddress(kaufland_shipping_address)
                                except ValueError as Error:
                                    neworder.bill_address = None
                                    neworder.shipment_address = None
                                    neworder.has_errors = True
                                    neworder.messages = Error

                                neworder.payment_status = 'paid'
                                try:
                                    default_payment = SellAssistPayment.objects.get(default=True)
                                except SellAssistPayment.DoesNotExist:
                                    default_payment = SellAssistPayment()
                                    default_payment.title = 'Płatność online'
                                    default_payment.clean()
                                    default_payment.save()
                                try:
                                    default_shipment = SellAssistPayment.objects.get(default=True)
                                except SellAssistPayment.DoesNotExist:
                                    default_shipment = SellAssistShipment()
                                    default_shipment.title = 'Płatność online'
                                    default_shipment.clean()
                                    default_shipment.save()

                                neworder.payment = default_payment
                                neworder.shipment = default_shipment

                                neworder.status = 1
                                neworder.date = {}
                                neworder.shipment_price = shipping_rate
                                try:
                                    neworder.create = datetime.datetime.fromisoformat(order_data.get('ts_created_iso'))
                                except Exception as Error:
                                    neworder.create = datetime.datetime.now()

                                if delivery_time_min is not None:
                                    try:
                                        default_delivery_time = GlobalSettings.objects.get(name='default_delivery_time')
                                    except GlobalSettings.DoesNotExist:
                                        default_delivery_time = 2
                                    delivery_time_min = delivery_time_min - default_delivery_time
                                    neworder.deadline = neworder.create + datetime.timedelta(days=delivery_time_min)

                                neworder.marketplace = 'kaufland' + order_data.get("storefront")
                                neworder.clean()
                                neworder.save()

                                # TODO: there is more than units. I have to check that product can have multiple instance too.
                                carts = SellAssistCart.objects.filter(order=neworder)

                                if len(carts) == 0:
                                    for unit in units:
                                        kaufland_product = unit.get('product')
                                        product = None

                                        eans = kaufland_product.get('eans')

                                        for ean in eans:
                                            products = SellAssistRegisteredProduct.objects.filter(ean=ean)
                                            if len(products) > 0:
                                                product = products[0]

                                        if product is None:
                                            product = SellAssistUnknownProduct()
                                            product.name = kaufland_product.get('title')
                                            product.ean = eans[0] if len(eans)>0 else ''
                                            product.sku = unit.get('id_offer')
                                            product.save()

                                        try:
                                            newcart = SellAssistCart.objects.get(order=neworder, product=product)
                                            newcart.quantity += 1
                                            newcart.save()
                                        except SellAssistCart.DoesNotExist:
                                            newcart = SellAssistCart()
                                            newcart.quantity = 1
                                            newcart.order = neworder
                                            newcart.price = float(unit.get('price') / 100)
                                            newcart.product = product
                                            newcart.additional_information = unit.get('fulfillment_type')
                                            newcart.save()


    """Note that You can set as sent for every unit in order"""
    def setassent(self,order_data, carrier_code,tracking):
        method = 'PATCH'
        for order_unit in order_data:
            id_order_unit = order_unit.get('id_order_unit')
            if id_order_unit is not None:
                uri = f'/order-units/{id_order_unit}/send'
                body = {}
                body['carrier_code'] = carrier_code
                body['tracking_numbers'] = tracking
                body = json.dump(body)
                self.callapi(uri,body,method)



class KauflandOffer(MarketplaceOffer):
    condition = (
        ('new', 'NEW'),
        ('used_as_new', 'USED___AS_NEW'),
    )

    status = (
        ('available', 'AVAILVABLE'),
        ('onhold', 'ONHOLD'),
    )

    storefront = (
        ('de', 'de'),
        ('sk', 'sk'),
        ('cz', 'cz'),
    )

    id_product = models.CharField(max_length=200)
    id_unit = models.CharField(max_length=200)
    product = models.ForeignKey(SellAssistProduct, on_delete=models.SET_NULL, null=True, default=None)
    condition = models.CharField(max_length=20,choices=condition, default='new')
    status = models.CharField(max_length=20,choices=status, default='available')
    _listing_price = models.FloatField()
    minimum_price = models.FloatField()
    _amount = models.IntegerField()
    note = models.CharField(max_length=50)
    id_offer = models.CharField(max_length=50)
    id_warehouse = models.CharField(max_length=20)
    id_shipping_group = models.CharField(max_length=20)
    storefront = models.CharField(max_length=2,choices=storefront)


    @property
    def handling_time(self):
        return self._handling_time

    @handling_time.setter
    def handling_time(self,handling_time):
        self._handling_time = handling_time
        if handling_time != self._handling_time:
            self.updateoffer()


    @property
    def listing_price(self):
        return self._listing_price

    @listing_price.setter
    def listing_price(self,listing_price):
        self._listing_price = listing_price
        if listing_price != self._listing_price:
            pass

    @property
    def amount(self):
        return self._amount

    @amount.setter
    def amount(self,amount):
        self._amount = amount
        if amount != self._amount:
            pass


    def return_json(self):
        obj_json = {}
        obj_json['id_product'] = self.id_product
        obj_json['ean'] = self.ean
        obj_json['condition'] = self.condition
        obj_json['listing_price'] = self.listing_price if self.listing_price == 0 else int(self.listing_price*100)
        obj_json['minimum_price'] = self.minimum_price if self.minimum_price == 0 else int(self.minimum_price*100)
        obj_json['amount'] = self.amount
        obj_json['note'] = self.note
        obj_json['id_offer'] = self.id_offer
        obj_json['handling_time'] = self.handling_time
        obj_json['id_warehouse'] = self.id_warehouse
        obj_json['id_shipping_group'] = self.id_shipping_group
        obj_json['storefront'] = self.storefront
        return obj_json

    def updateoffer(self):
        api = KauflandAPI.objects.first()
        if api is not None:
            offer_json = self.return_json()
            if offer_json.get('listing_price') == 0:
                del offer_json['listing_price']
            if offer_json.get('minimum_price') == 0:
                del offer_json['minimum_price']
            try:
                api.updateoffer(offer_json)
            except Exception as Error:
                self.has_error = True
                self.message = Error
                self.save()


    def findproduct(self):
        api = KauflandAPI.objects.first()
        if api is not None:
            if self.ean is None:
                product = api.getproduct(self.id_product,self.storefront)
                if product is not None:
                    product_data = product.get('data')
                    if product_data is not None:
                        eans = product_data.get('eans')
                        product = None
                        for ean in eans:
                            product = SellAssistRegisteredProduct.objects.filter(ean=ean).first()
                            if product:
                                break
                        if product is not None:
                            self.ean = product.ean
                            self.product = product
                        else:
                            self.ean = eans[0]
            else:
                product = SellAssistRegisteredProduct.objects.filter(ean=self.ean).first()
                if product is not None:
                    self.product = product
        self.save()





    def registeroffers(self):

        api = KauflandAPI.objects.first()


        storefronts = api.getstorefronts()
        storefronts_data = storefronts.get('data')
        if storefronts_data is not None:
            for storefront in storefronts_data:
                total_offers = 1
                if api:
                    body = {}
                    body['storefront'] = storefront
                    body['limit'] = '1'
                    downloaded = 0
                    read = True
                    while read:
                        offers = api.getoffers(body)
                        print(offers)
                        if offers not in [None, '']:
                            offers_data = offers.get('data')
                            pagination = offers.get('pagination')
                            if pagination is not None:
                                #total_offers = pagination.get('total')
                                offset = pagination.get('offset')
                                if None not in [total_offers, offset, offers_data]:
                                    if offers_data is not None:
                                        for offer in offers_data:
                                            downloaded +=1
                                            try:
                                                KauflandOffer.objects.get(id_unit=offer.get('id_unit'))
                                            except KauflandOffer.DoesNotExist:
                                                newoffer = KauflandOffer()
                                                newoffer.id_product = offer.get('id_product')
                                                newoffer.currency = offer.get('currency')
                                                newoffer.id_unit = offer.get('id_unit')
                                                newoffer.handling_time = offer.get('handling_time')
                                                newoffer.id_warehouse = offer.get('id_warehouse')
                                                newoffer.id_shipping_group = offer.get('id_shipping_group')
                                                newoffer.id_offer = offer.get('id_offer')
                                                newoffer.amount = offer.get('amount')
                                                newoffer.status = offer.get('status')
                                                newoffer.condition = offer.get('condition')
                                                newoffer.storefront = offer.get('storefront')
                                                newoffer.listing_price = float(offer.get('listing_price'))/100 if offer.get('listing_price') is not None else 0
                                                newoffer.minimum_price = float(offer.get('minimum_price'))/100 if offer.get('minimum_price') is not None else 0
                                                newoffer.note = offer.get('note') if offer.get('note') is not None else ''
                                                newoffer.save()
                                                newoffer.findproduct()

                                if downloaded < total_offers:
                                    body['offset'] = str(offset +1)
                                else:
                                    read = False






