from django import forms
from django.conf import settings

from .cart import MAX_QUANTITY
from .models import Order, Product

ZERO_DECIMAL_CURRENCIES = {'FCFA', 'CFA', 'XOF', 'XAF', 'GNF'}


class ProductForm(forms.ModelForm):
    """Formulaire admin pour créer/modifier un article de la boutique"""
    class Meta:
        model = Product
        fields = ('name', 'price', 'description', 'image', 'available')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if settings.SHOP_CURRENCY.upper() in ZERO_DECIMAL_CURRENCIES and price != price.to_integral_value():
            raise forms.ValidationError(f'Le prix en {settings.SHOP_CURRENCY} doit être un nombre entier.')
        return price


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'city')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'minlength': 2}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'minlength': 2}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+225 07 00 00 00 00'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def _clean_name(self, field):
        value = self.cleaned_data[field].strip()
        if len(value) < 2:
            raise forms.ValidationError('Au moins 2 caractères.')
        return value

    def clean_first_name(self):
        return self._clean_name('first_name')

    def clean_last_name(self):
        return self._clean_name('last_name')


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status',)
        widgets = {'status': forms.Select(attrs={'class': 'form-select'})}


class CartQuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=0, max_value=MAX_QUANTITY)
