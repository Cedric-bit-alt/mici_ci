from django.db import models


class ContactMessage(models.Model):
    """Modèle pour les messages de contact"""
    name = models.CharField(max_length=100, verbose_name='Nom')
    email = models.EmailField(verbose_name='Email')
    subject = models.CharField(max_length=200, verbose_name='Sujet')
    message = models.TextField(verbose_name='Message')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    is_read = models.BooleanField(default=False, verbose_name='Lu')
    
    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Message de {self.name} - {self.subject}'
