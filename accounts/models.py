from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Modèle utilisateur personnalisé avec rôle"""
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Membre', 'Membre'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='Membre',
        verbose_name='Rôle'
    )
    bio = models.TextField(blank=True, null=True, verbose_name='Biographie')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Avatar')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.username
    
    def is_admin_user(self):
        """Vérifie si l'utilisateur est un admin"""
        return self.role == 'Admin' or self.is_superuser
    
    def is_member_user(self):
        """Vérifie si l'utilisateur est un membre"""
        return self.role == 'Membre'
