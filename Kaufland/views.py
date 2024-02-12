from django.shortcuts import render
from .models import KauflandAPI, KauflandOffer,KauflandShippingMethod
from .tasks import checkforupdates
from Octopus.celery import app
# Create your views here.


def getorders(request):
    try:
        kapi = KauflandAPI.objects.first()
        if kapi:
            kapi.createorders()
            context = {'message':'Orders created successfully'}
            return render(request,'simple.html',context=context)
        else:
            raise KauflandAPI.DoesNotExist
    except KauflandAPI.DoesNotExist:

        context = {'message':'Kaufland API settings doesn\'t exist'}
        return render(request,'simple.html',context=context,status=200)

def getunits(request):
    try:
        #print(KauflandOffer().registeroffers())
        kaufland_offer = KauflandOffer.objects.first()
        kaufland_offer.findproduct()

        context = {'message':'Orders created successfully'}
        return render(request,'simple.html',context=context)

    except KauflandAPI.DoesNotExist:
        context = {'message':'Kaufland API settings doesnt exist'}
        return render(request,'simple.html',context=context,status=204)


def showtasks(request):
    print(app.conf.beat_schedule)
    app.conf.beat_schedule = {'task':'printsth','schedule':10}
    print(app.conf.beat_schedule)

def checkoffers(request):
    checkforupdates()
    context = {'message': 'Orders created successfully'}
    return render(request, 'simple.html', context=context)


def registershippings(request):
    KauflandShippingMethod().registershipping()
    context = {'message': 'Orders created successfully'}
    return render(request, 'simple.html', context=context)