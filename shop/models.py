import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Product(models.Model):
    """Article religieux vendu dans la boutique"""
    name = models.CharField(max_length=200, verbose_name='Nom')
    slug = models.SlugField(unique=True, max_length=220, verbose_name='Slug')
    description = models.TextField(verbose_name='Détails')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='Prix',
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Image')
    available = models.BooleanField(default=True, verbose_name='Disponible')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Date de modification')

    class Meta:
        verbose_name = 'Article de la boutique'
        verbose_name_plural = 'Articles de la boutique'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'article'
            slug = base
            counter = 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.slug})


class Order(models.Model):
    """Commande validée par un utilisateur connecté"""
    PENDING = 'pending'
    PAID = 'paid'
    FAILED = 'failed'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (PENDING, 'En attente de paiement'),
        (PAID, 'Payée'),
        (FAILED, 'Paiement échoué'),
        (SHIPPED, 'Expédiée'),
        (DELIVERED, 'Livrée'),
        (CANCELLED, 'Annulée'),
    ]
    PAYABLE_STATUSES = (PENDING, FAILED)
    STATUS_BADGES = {
        PENDING: 'warning text-dark',
        PAID: 'success',
        FAILED: 'danger',
        SHIPPED: 'info text-dark',
        DELIVERED: 'primary',
        CANCELLED: 'secondary',
    }

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders',
        verbose_name='Client',
    )
    first_name = models.CharField(max_length=100, verbose_name='Prénom')
    last_name = models.CharField(max_length=100, verbose_name='Nom')
    email = models.EmailField(verbose_name='Email')
    phone = models.CharField(max_length=30, verbose_name='Téléphone')
    address = models.CharField(max_length=255, verbose_name='Adresse de livraison')
    city = models.CharField(max_length=100, verbose_name='Ville')
    total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Total')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, verbose_name='Statut')

    merchant_transaction_id = models.CharField(
        max_length=30, unique=True, null=True, blank=True, verbose_name='Référence de paiement'
    )
    cinetpay_transaction_id = models.CharField(max_length=100, blank=True, verbose_name='Transaction CinetPay')
    notify_token = models.CharField(max_length=255, blank=True, editable=False)
    payment_url = models.URLField(max_length=500, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date de commande')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Dernière mise à jour')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Payée le')

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-created_at']

    def __str__(self):
        return f'Commande n°{self.id}'

    def get_absolute_url(self):
        return reverse('shop:order_detail', kwargs={'reference': self.reference})

    @property
    def is_payable(self):
        return self.status in self.PAYABLE_STATUSES

    @property
    def status_badge(self):
        return self.STATUS_BADGES.get(self.status, 'secondary')


class OrderItem(models.Model):
    """Ligne de commande : nom et prix figés au moment de la commande"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Commande')
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items', verbose_name='Article'
    )
    product_name = models.CharField(max_length=200, verbose_name='Article')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Prix unitaire')
    quantity = models.PositiveIntegerField(verbose_name='Quantité')

    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'

    def __str__(self):
        return f'{self.quantity} × {self.product_name}'

    @property
    def subtotal(self):
        return self.price * self.quantity
