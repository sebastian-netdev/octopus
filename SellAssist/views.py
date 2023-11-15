from django.shortcuts import render
from .models import SellAssistOrder
# Create your views here.



def validateorders(request):
    try:
        orders = SellAssistOrder.objects.filter(registered=False,validated=False)
        counter = 0
        for order in orders:
            order.validateorder()
            if order.validated:
                counter += 1
        context = {'message':f'Orders {counter}/{len(orders)} validated'}
        return render(request,'simple.html',context=context)
    except Exception as Error:
        context = {'message':f'{Error}'}
        return render(request,'simple.html',context=context,status=403)

def registerorders(request):
    try:
        orders = SellAssistOrder.objects.filter(registered=False,validated=True)
        counter = 0
        for order in orders:
            order.registerorder()
            break
        context = {'message':f'Orders {counter}/{len(orders)} validated'}
        return render(request,'simple.html',context=context)
    except UnicodeError as Error:
        print(Error)
        context = {'message':f'{Error}'}
        return render(request,'simple.html',context=context,status=404)




