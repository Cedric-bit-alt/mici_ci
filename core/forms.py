from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    """Formulaire de contact"""
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'subject', 'message')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
        labels = {
            'name': 'Nom',
            'email': 'Email',
            'subject': 'Sujet',
            'message': 'Message',
        }

