from celery import Celery,shared_task
from .models import MarketplaceOffer,APIKey
from django.core.handlers.wsgi import WSGIRequest
app = Celery()



def authrequired(func):

    def wrapper(*args, **kwargs):
        if len(args)>0:
            request = args[0]
            if isinstance(request,WSGIRequest):
                key = request.GET.get('apikey')
                apikey = None
                if key is not None:
                    try:
                        apikey = APIKey.objects.get(key=key)
                    except APIKey.DoesNotExist:
                        apikey = None
                if apikey is not None:
                    return func(*args,**kwargs)
                else:
                    raise ValueError
    return wrapper
