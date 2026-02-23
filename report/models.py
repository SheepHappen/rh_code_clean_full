from django.db import models

from core.models import UuidPrimaryKeyModel


class pdfContactDetail(UuidPrimaryKeyModel):
    address_line_1 = models.CharField('Address line 1', max_length=255)
    address_line_2 = models.CharField('Address line 2', max_length=255, blank=True, null=True)
    address_line_3 = models.CharField('Town/City', max_length=255)
    address_line_4 = models.CharField('County', max_length=255)
    post_code = models.CharField('post code', max_length=10)
    phone = models.CharField('phone', max_length=40)
    email = models.EmailField(max_length=255)

    def __str__(self):
        return self.address_line_1
