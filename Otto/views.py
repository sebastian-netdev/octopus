import datetime
import time
from SellAssist.models import SellAssistOrder, SellAssistPayment
from django.shortcuts import render
from .models import OttoAPI, OttoOffers, OttoOrders
# Create your views here.



def gettoken(request):
    api = OttoAPI.objects.first()

    api.gettoken()


def getoffers(request):

    offers = OttoOffers()
    offers.getoffers(100)

def findproducts(request):

    offers = OttoOffers()
    offers.findproducts()


def getorders(request,forceupdate=False):
    date_from = datetime.datetime.now()- datetime.timedelta(days=7)
    date_from.isoformat('T')
    order_list = OttoOrders().getorderslist(date_from=date_from.isoformat('T'), limit=2, status='PROCESSABLE')
    ottoorders = order_list.get('resources')
    links = order_list.get('links')

    print(ottoorders)
    for ottoorder in ottoorders:
        if ottoorder is not None:
            ottoordernumber = ottoorder.get('orderNumber')
            try:
                order = SellAssistOrder.objects.get(marketplace_id=ottoordernumber)
            except SellAssistOrder.DoesNotExist:
                order = None
            if order is None:
                OttoOrders().createorder(ottoorder)
                break











