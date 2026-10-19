from django import forms
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Formulaire pour créer/modifier un article"""
    class Meta:
        model = Post
        fields = ('title', 'content', 'image')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    """Formulaire pour créer un commentaire"""
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Votre commentaire...'
            }),
        }
        labels = {
            'content': 'Commentaire',
        }

