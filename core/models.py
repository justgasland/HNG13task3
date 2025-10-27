from django.db import models
from django.utils import timezone


class Country(models.Model):
    id= models.AutoField(primary_key=True)
    name=models.CharField(max_length=100 ,)
    capital = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    population = models.IntegerField()
    currency_code = models.CharField(max_length=10, blank=True, null=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estimated_gdp = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    flag_url = models.URLField(max_length=200, blank=True, null=True)
    last_refreshed_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
class RefreshStatus(models.Model):
    last_refreshed_at = models.DateTimeField(default=timezone.now)
    total_countries = models.IntegerField(default=0)

    class Meta:
        db_table = 'refresh_status'
# Create your models here.
