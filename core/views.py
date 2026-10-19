from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm


def home(request):
    """Vue pour la page d'accueil"""
    from blog.models import Post
    
    # Articles récents (3 derniers)
    recent_posts = Post.objects.all()[:3]
    
    context = {
        'recent_posts': recent_posts,
    }
    return render(request, 'core/home.html', context)


def about(request):
    """Vue pour la page À propos"""
    return render(request, 'core/about.html')


def contact(request):
    """Vue pour la page Contact"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            messages.success(request, 'Votre message a été envoyé avec succès. Nous vous répondrons bientôt.')
            return redirect('core:contact')
    else:
        form = ContactForm()
    
    return render(request, 'core/contact.html', {'form': form})


def privacy(request):
    """Vue pour la page Politique de confidentialité"""
    return render(request, 'core/privacy.html')
