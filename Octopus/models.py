from django.db import models

# Create your models here.



class Marketplace(models.Model):
    name = models.CharField(max_length=50)


class GlobalSettings(models.Model):
    name = models.CharField(max_length=200)
    value = models.TextField()


class MarketplaceOffer(models.Model):


    def updatehandlingtime(self):
        pass
    def updatequantity(self):
        pass
    def updateprice(self):
        pass

    def updateoffer(self):
        pass


