from django.db import models

# Create your models here.



class Marketplace(models.Model):
    name = models.CharField(max_length=50)


class GlobalSettings(models.Model):
    name = models.CharField(max_length=200)
    value = models.TextField()


class MarketplaceOffer(models.Model):

    ean = models.CharField(max_length=20)
    has_error = models.BooleanField(default=False)
    currency = models.CharField(max_length=3)
    message = models.TextField()
    _handling_time = models.IntegerField()
    last_update = models.DateField(auto_now=True)

    def updateoffer(self):
        pass


