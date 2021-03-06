from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django import forms

import jwt

from lib.sellers.models import Seller

from .constants import BLUEVIA_CURRENCIES

# TODO find out how this is populated.
secret = 'some-unknown'


class PayValidation(forms.Form):
    aud = forms.CharField()
    typ = forms.CharField()
    amount = forms.DecimalField(min_value=Decimal('0.1'),
                                max_value=Decimal('5000'))
    app_name = forms.CharField()
    app_description = forms.CharField()
    chargeback_url = forms.URLField()
    currency = forms.ChoiceField(choices=[(c, c) for c in
                                          BLUEVIA_CURRENCIES.keys()])
    postback_url = forms.URLField()
    product_data = forms.CharField()
    seller = forms.ModelChoiceField(queryset=Seller.objects.all(),
                                    to_field_name='uuid')

    def clean_seller(self):
        seller = self.cleaned_data['seller']
        try:
            self.cleaned_data['id'] = seller.bluevia.bluevia_id
        except ObjectDoesNotExist:
            pass
        if not self.cleaned_data.get('id', ''):
            raise forms.ValidationError('No bluevia id found.')
        return seller

    def clean(self):
        data = self.cleaned_data
        if not data.get('typ', '').startswith(data.get('aud', '')):
            raise forms.ValidationError('aud and type mismatch.')
        data['secret'] = secret
        return data


class JWTValidation(forms.Form):
    jwt = forms.CharField()
    seller = forms.ModelChoiceField(queryset=Seller.objects.all(),
                                    to_field_name='uuid')

    def clean_jwt(self):
        data = self.cleaned_data['jwt']
        try:
            jwt.decode(data.encode('ascii'), secret)
        except jwt.DecodeError as err:
            raise forms.ValidationError(err.message)

        self.cleaned_data['valid'] = True
        return data
