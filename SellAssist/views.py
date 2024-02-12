from django.shortcuts import render
from .models import SellAssistOrder,SellAssistAPI
from .tasks import stockupdate,registerproducts,getorderfields
from Octopus.tasks import authrequired
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
        orders = SellAssistOrder.objects.filter(registered=False,validated=True)[:1]
        counter = 0
        for order in orders:
            print(order.id)
            print(order.return_json())
            order.registerorder()
            break
        context = {'message':f'Orders {counter}/{len(orders)} validated'}
        return render(request,'simple.html',context=context)
    except UnicodeError as Error:
        print(Error)
        context = {'message':f'{Error}'}
        return render(request,'simple.html',context=context,status=404)



def getorders(request):
    try:
        api = SellAssistAPI.objects.first()
        print(api.getorders())
        context = {'message':f'Orders downloaded'}
        return render(request,'simple.html',context=context)
    except UnicodeError as Error:
        print(Error)
        context = {'message':f'{Error}'}
        return render(request,'simple.html',context=context,status=404)

def getstocks(request):
    stockupdate()
    context = {'message': f'Stock update proces finished'}
    return render(request, 'simple.html', context=context)


def getproducts(request):
    registerproducts()
    context = {'message': f'Product update proces finished'}
    return render(request, 'simple.html', context=context)


def getorderextrafields(request):
    getorderfields()
    context = {'message': f'Order fields proces finished'}
    return render(request, 'simple.html', context=context)

@authrequired
def setassent(request):
    if request.method == 'GET':
        status = 200
        context = {}

        order_id = request.GET.get('order_id')
        if order_id is not None:
            context['message'] = f'Order({order_id}) has been marked as sent'
            try:
                order = SellAssistOrder.objects.get(sellassist_id=order_id)


                context['message'] = f'Order {order_id} found in database'


            except SellAssistOrder.DoesNotExist:
                status = 404
                context['message'] = f'Order({order_id}) doesn\'t exist in database'
        else:
            status = 404
            context['message'] = f'Order id can not be None'


        return render(request, 'simple.html', context=context,status=status)
