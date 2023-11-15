from django.shortcuts import render
from .models import KauflandAPI
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
        kapi = KauflandAPI.objects.first()
        storefronts = ['de']

        for storefront in storefronts:
            body = {'storefront':storefront}
            print(kapi.getoffers(body=body))

        context = {'message':'Orders created successfully'}
        return render(request,'simple.html',context=context)

    except KauflandAPI.DoesNotExist:
        context = {'message':'Kaufland API settings doesnt exist'}
        return render(request,'simple.html',context=context,status=204)