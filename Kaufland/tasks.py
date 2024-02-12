import time
from Octopus.celery import app as celery_app
from Kaufland.models import KauflandAPI,KauflandOffer
from celery import shared_task

@shared_task
def registeroffers():
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
                    if offers not in [None, '']:
                        offers_data = offers.get('data')
                        pagination = offers.get('pagination')
                        if pagination is not None:
                            # total_offers = pagination.get('total')
                            offset = pagination.get('offset')
                            if None not in [total_offers, offset, offers_data]:
                                if offers_data is not None:
                                    for offer in offers_data:
                                        downloaded += 1
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
                                            newoffer.listing_price = float(
                                                offer.get('listing_price')) / 100 if offer.get(
                                                'listing_price') is not None else 0
                                            newoffer.minimum_price = float(
                                                offer.get('minimum_price')) / 100 if offer.get(
                                                'minimum_price') is not None else 0
                                            newoffer.note = offer.get('note') if offer.get('note') is not None else ''
                                            newoffer.save()
                                            newoffer.findproduct()

                            if downloaded < total_offers:
                                body['offset'] = str(offset + 1)
                            else:
                                read = False

@shared_task
def updateoffers():
    offers = KauflandOffer.objects.filter(toupdate=True)
    for offer in offers:
        if offer.product is not None:
            if offer.toupdate:
                print(offer)
                offer.updateoffer()

@shared_task
def checkforupdates():
    offers = KauflandOffer.objects.exclude(product__isnull=True)
    for offer in offers:
        if offer.product.quantity != offer.quantity:
            offer.quantity = offer.product.quantity
            offer.save()


@shared_task
def findproductrelations():
    offers = KauflandOffer.objects.exclude(product__isnull=False)
    for offer in offers:
        try:
            offer.findproduct()
        except Exception as Error:
            offer.has_error = True
            offer.message = Error
            offer.save()







