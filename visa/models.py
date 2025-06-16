from django.db import models

from account.models import CustomUser
from command.models import BaseModel


# Create your models here.
class Visa(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class VisaRegister(BaseModel):
    visa = models.ForeignKey(Visa, on_delete=models.CASCADE,related_name='register_visa')

    visa_unique_code = models.CharField(max_length=10, unique=True,help_text='visa code',verbose_name='visa code')

    user : "CustomUser" = models.ForeignKey("account.CustomUser", on_delete=models.CASCADE,related_name='register_visa')
    def __str__(self):
        return self.visa.name