from django.shortcuts import render
from .models import KauflandAPI, KauflandOffer
# Create your views here.


def getorders(request):
    try:
        kapi = KauflandAPI.objects.first()
        kapi.createorders()
        context = {'message':'Orders created successfully'}
        return render(request,'simple.html',context=context)

    except KauflandAPI.DoesNotExist:
        context = {'message':'Kaufland API settings doesnt exist'}
        return render(request,'simple.html',context=context,status=204)

def getunits(request):
    try:

        #print(KauflandOffer().registeroffers())
        kaufland_offer = KauflandOffer.objects.first()
        print(kaufland_offer.id_unit)
        kaufland_offer.findproduct()

        context = {'message':'Orders created successfully'}
        return render(request,'simple.html',context=context)

    except KauflandAPI.DoesNotExist:
        context = {'message':'Kaufland API settings doesnt exist'}
        return render(request,'simple.html',context=context,status=204)