import random
import string

from django.db import models
# Create your models here.



class Marketplace(models.Model):
    name = models.CharField(max_length=50)


class APIKey(models.Model):
    name = models.CharField(max_length=200)
    key = models.CharField(max_length=200,blank=200)

    def clean(self):
        type = ['d','l']
        apikey = ''
        max_len = 20
        for i in range(0,max_len):
            if random.choice(type) == 'd':
                apikey = apikey + random.choice(string.digits)
            else:
                apikey = apikey + random.choice(string.ascii_letters.upper())
        self.key = apikey



class GlobalSettings(models.Model):
    name = models.CharField(max_length=200)
    value = models.TextField()


class MarketplaceOffer(models.Model):
    name = models.CharField(max_length=300,null=True)
    ean = models.CharField(max_length=20,null=True)
    has_error = models.BooleanField(default=False)
    currency = models.CharField(max_length=3,default='EUR',null=True)
    message = models.TextField(blank=True)
    handling_time = models.IntegerField(default=1)
    last_update = models.DateField(auto_now=True)
    marketplace = models.CharField(max_length=200,null=True)
    toupdate = models.BooleanField(default=False)
    _quantity = models.IntegerField()
    #product = models.ForeignKey(SellAssist.models.SellAssistProduct, on_delete=models.SET_NULL,null=True)
    @property
    def quantity(self):
        return self._quantity

    @quantity.setter
    def quantity(self,quantity):
        if quantity > 0:
            if quantity != self._quantity:
                self._quantity = quantity
                if not self.toupdate:
                    self.toupdate = True
        else:
            self._quantity = 0

    class Meta:

        abstract = True

