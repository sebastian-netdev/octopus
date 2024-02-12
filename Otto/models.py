import datetime
import time

from django.core.exceptions import ValidationError
from Octopus.models import MarketplaceOffer
from SellAssist.models import SellAssistRegisteredProduct,SellAssistOrder,SellAssistPayment,SellAssistShipment,SellAssistAddress, SellAssistCountry
from django.db import models
import requests
from dateutil import parser as dateparser
import json
import pytz
# Create your models here.


class OttoAPI(models.Model):
    periods = (
        ('1h', '1h'),
        ('4h', '4h'),
        ('8h', '8h'),
        ('24', '24h'),
    )

    endpoint = models.CharField(max_length=200)
    username = models.CharField(max_length=200)
    password = models.CharField(max_length=200)
    access_token = models.TextField(blank=True)
    access_token_expire = models.DateTimeField(null=True,blank=True)
    refresh_token = models.TextField(blank=True)
    refresh_token_expire = models.DateTimeField(null=True,blank=True)

    def clean(self):
        apis = OttoAPI.objects.all()

        if len(apis) == 1:
            api = apis[0]
            if self.id != api.id:
                raise ValidationError('There is not place for more API keys')


    def gettoken(self):
        headers = {}
        headers['Content-Type'] = ' application/x-www-form-urlencoded'
        headers['Cache-Control'] = 'no-cache'
        body = {}
        body['username'] = self.username
        body['password'] = self.password
        body['grant_type'] = 'password'
        body['client_id'] = 'token-otto-api'

        uri = f"/v1/token"

        url = self.endpoint + uri

        token_expired = False


        try:
            if datetime.datetime.now(pytz.timezone('Europe/Warsaw')) > self.access_token_expire:
                token_expired = True
        except TypeError:
            token_expired = True

        if token_expired:
            try:
                response = requests.post(url, data=body)
            except Exception:
                response = None

            if response is not None and response.status_code == 200:
                data = json.loads(response.text)
                token = data.get('access_token')
                refresh_token = data.get('refresh_token')

                token_expire_delta = data.get('expires_in')
                refresh_token_expire_delta = data.get('refresh_expires_in')
                self.access_token_expire = datetime.datetime.now() + datetime.timedelta(seconds=token_expire_delta)
                self.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(seconds=refresh_token_expire_delta)
                self.access_token = token
                self.refresh_token = refresh_token
                self.save()
                return self.access_token
            else:
                self.access_token = ''
                self.refresh_token = ''
                self.access_token_expire = None
                self.refresh_token_expire = None
                self.save()

            return self.access_token
        else:
            return self.access_token

    def callapi(self,uri,method,body):
        token = self.gettoken()
        headers = {}
        headers['Authorization'] = f'Bearer {token}'
        headers['Accept'] = f'application/json'
        headers['X-Request-Timestamp'] = f'{datetime.datetime.now().isoformat("T")}'

        url = self.endpoint + uri
        response = None
        if method == 'POST':
            response = requests.post(url,data=body,headers=headers)
        elif method == 'GET':
            response = requests.get(url,headers=headers)


        if response is not None:
            if response.status_code in [200,207]:
                return json.loads(response.text)
            else:
                print(response.status_code)
                print(response.text)
                print(response.request.url)
                print(response.request.headers)
                print(response.request.method)



    def updatequantity(self,body):
        uri = 'v2/quantities'
        method = 'POST'
        response = self.callapi(uri,method,body)
        return response


    def getoffers(self,body=None, limit = None, page = None):
        uri = '/v3/products'

        params = [limit,page]

        for param in params:
            if param is not None:
                uri = uri + '?'

        if limit is not None:
            uri = uri + f'limit={limit}'
        if page is not None:
            uri = uri + f'page={page}'



        method = 'GET'
        body = body if body is not None else ''

        response = self.callapi(uri,method,body)
        return  response





class OttoOffers(MarketplaceOffer):

    status = (
        ('available', 'AVAILABLE'),
        ('not available', 'NOT AVAILABLE'),
    )

    product = models.ForeignKey(SellAssistRegisteredProduct, on_delete=models.SET_NULL, null=True, default=None,blank=True)
    status = models.CharField(max_length=20,choices=status, default='available')
    price = models.FloatField()
    sku = models.CharField(max_length=50)
    period = models.IntegerField(default=None,null=True)
    delivery_type = models.CharField(max_length=50,null=True)

    def registeroffer(self,offer,update_offers=False):

        if offer is not None:
            newoffer = None
            ean = offer.get('ean')

            if ean is not None:
                try:
                    newoffer = OttoOffers.objects.get(ean=ean)
                    if not update_offers:
                        newoffer = None
                except OttoOffers.DoesNotExist:
                    newoffer = OttoOffers()

            if newoffer is not None:
                newoffer.ean = ean
                newoffer.sku = offer.get('sku')
                try:
                    delivery_time = offer.get('delivery').get('delivery_time')
                except AttributeError:
                    delivery_time = None
                newoffer.handling_time = delivery_time if delivery_time is not None else 30

                try:
                    delivery_type = offer.get('delivery').get('type')
                except AttributeError:
                    delivery_type = None

                newoffer.delivery_type = delivery_type

                newoffer.marketplace = 'otto'
                # try:
                #     quantity = offer.get('order').get('maxOrderQuantity').get('quantity')
                # except AttributeError:
                #     quantity = None
                #
                newoffer.quantity = 0

                try:
                    period = offer.get('order').get('maxOrderQuantity').get('periodInDays')
                except AttributeError:
                    period = None

                newoffer.period = period

                try:
                    price = offer.get('pricing').get('standardPrice').get('amount')
                except AttributeError:
                    price = None

                newoffer.price = price if price is not None else 0


                try:
                    currency = offer.get('pricing').get('standardPrice').get('currency')
                except AttributeError:
                    currency = None
                newoffer.currency = currency
                newoffer.save()


    def getoffers(self, offers_limit=10000):
        request_limit = 100
        api = OttoAPI.objects.first()
        next = True
        offers_counter = 0
        while next:
            response = api.getoffers(limit=request_limit)
            if response is not None:
                offers = response.get('productVariations')

                if offers is not None:
                    offers_counter = offers_counter + len(offers)
                    links = response.get('links')
                    pages = []
                    for link in links:
                        rel = link.get('rel')
                        pages.append(link.get('rel'))

                    if 'next' not in pages:
                        next = False

                    if offers_counter >= offers_limit:
                        next=False

                    for offer in offers:
                        self.registeroffer(offer)

    def findproducts(self):
        offers = OttoOffers.objects.filter(product=None)
        for offer in offers:
            product = SellAssistRegisteredProduct.objects.filter(ean=offer.ean).first()
            if product is not None:
                offer.product = product
                offer.save()

    def updateoffersquantity(self):
        limit = 200
        offers = OttoOffers.objects.exclude(product=None)
        api = OttoAPI.objects.first()
        if api is not None:
            offerstoupdate = []
            for offer in offers:
                if offer.quantity != offer.product.quantity:
                    offerstoupdate.append(offer)
                    offer.quantity = offer.product.quantity if offer.product.quantity >= 0 else 0
                    offer.save()

            error_list = []
            offerspool = []
            for offertoupdate in offerstoupdate:
                offerspool.append({'sku':offertoupdate.sku,'lastModified':f'{datetime.datetime.now().isoformat("T")}','quantity':offertoupdate.quantity})
                if len(offerspool) == 200:
                    response = api.updatequantity(offerspool)
                    offerspool = []
                    if response is not None and isinstance(response,dict):
                        errors = response.get('errors')
                        if errors is not None and isinstance(errors,dict):
                            for error in errors:
                                error_list.append(error.get('title'))

            if len(offerspool) > 0:
                response = api.updatequantity(offerspool)
                if response is not None and isinstance(response, dict):
                    errors = response.get('errors')
                    if errors is not None and isinstance(errors, dict):
                        for error in errors:
                            error_list.append(error.get('title'))

class OttoOrders():

    def getordersdata(self,order_number):
        uri = f'/v4/orders/{order_number}'
        method = 'GET'
        body = ''

        api = OttoAPI.objects.first()
        response = api.callapi(uri, method, body)
        return response

    def getorderslist(self,date_from=None, limit=None, status = None):
        uri = f'/v4/orders'
        for element in [date_from,limit]:
            if element is not None:
                uri = uri + '?'
                break


        if date_from is not None:
            uri = uri +f'fromOrderDate={date_from}'

        if limit is not None:
            uri = uri + f'&limit={limit}'

        if status is not None:
            uri = uri + f'&fulfillmentStatus={status}'

        method = 'GET'
        body = ''

        api = OttoAPI.objects.first()
        response  = api.callapi(uri,method,body)
        return response

    def convertaddress(self,address):
        newaddress = SellAssistAddress()
        newaddress.name = address.get('firstName')
        newaddress.surname = address.get('lastName')
        newaddress.street = address.get('street')
        newaddress.home_number = address.get('houseNumber')
        newaddress.flat_number = address.get('addition') if address.get('addition') is not None else ''
        newaddress.city = address.get('city')
        newaddress.state = ''
        newaddress.phone = address.get('phoneNumber') if address.get('phoneNumber') is not None else ''
        country_code = address.get('countryCode')
        country = None
        if country_code is not None:
            country = SellAssistCountry.objects.filter(code = country_code).first()
            if country is None:
                country = SellAssistCountry()
                country.code = country_code
                country.save()
        newaddress.country = country
        newaddress.company_name = ''
        newaddress.company_nip = ''
        newaddress.save()
        return newaddress

    def createorder(self,orderdata):
        order = SellAssistOrder()
        order.create = dateparser.parse(orderdata.get('orderDate'))
        order.payment_status = 'paid'
        order.marketplace = 'otto'
        shipments = orderdata.get('initialDeliveryFees')
        shipment_amount = 0
        shipment_name = None
        for shipment in shipments:
            shipment_name = shipment.get('name')
            shipment_details = shipment.get('deliveryFeeAmount')
            amount = shipment_details.get('amount')
            if amount is not None:
                shipment_amount = shipment_amount + amount

        sellassistshipment = None
        if shipment_name is not None:
            sellassistshipment = SellAssistShipment.objects.filter(title=shipment_name).first()
            if sellassistshipment is None:
                sellassistshipment = SellAssistShipment()
                sellassistshipment.title = shipment_name
                sellassistshipment.save()
        order.shipment = sellassistshipment


        order.shipment_price = shipment_amount
        order_pos = orderdata.get('positionItems')
        deadline = None
        units = None
        for element in order_pos:
            if element.get('expectedDeliveryDate') is not None:
                deadline = dateparser.parse(element.get('expectedDeliveryDate'))
                break

        order.deadline = deadline



        payment = orderdata.get('payment')
        payment_method = payment.get('paymentMethod')
        sellassistpayment = None
        if payment_method is not None:
            sellassistpayment = SellAssistPayment.objects.filter(title=payment_method).first()
            if sellassistpayment is None:
                sellassistpayment = SellAssistPayment()
                sellassistpayment.title = payment_method
                sellassistpayment.save()

        order.payment = sellassistpayment
        billaddress = orderdata.get('invoiceAddress')
        shippingaddress = orderdata.get('deliveryAddress')
        order.bill_address = self.convertaddress(billaddress)
        order.shipment_address = self.convertaddress(shippingaddress)
        order.save()


