from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class Post(models.Model):
    """Modèle pour les articles du blog"""
    title = models.CharField(max_length=200, verbose_name='Titre')
    slug = models.SlugField(unique=True, max_length=200, verbose_name='Slug')
    content = models.TextField(verbose_name='Contenu')
    image = models.ImageField(upload_to='posts/', blank=True, null=True, verbose_name='Image')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Auteur'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Date de modification')
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='post_likes',
        blank=True,
        verbose_name='Likes'
    )
    
    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Génère automatiquement le slug à partir du titre"""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Retourne l'URL de l'article"""
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    def get_likes_count(self):
        """Retourne le nombre de likes"""
        return self.likes.count()
    
    def is_liked_by(self, user):
        """Vérifie si l'article est liké par un utilisateur"""
        if user.is_authenticated:
            return self.likes.filter(id=user.id).exists()
        return False


class Comment(models.Model):
    """Modèle pour les commentaires"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Article'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Utilisateur'
    )
    content = models.TextField(verbose_name='Contenu')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    approved = models.BooleanField(default=True, verbose_name='Approuvé')
    
    class Meta:
        verbose_name = 'Commentaire'
        verbose_name_plural = 'Commentaires'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Commentaire de {self.user.username} sur {self.post.title}'
