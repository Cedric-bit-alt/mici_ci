from django.urls import path

from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('article/ajouter/', views.product_create, name='product_create'),
    path('article/<slug:slug>/', views.product_detail, name='product_detail'),
    path('article/<slug:slug>/modifier/', views.product_edit, name='product_edit'),
    path('article/<slug:slug>/supprimer/', views.product_delete, name='product_delete'),
    path('panier/', views.cart_detail, name='cart_detail'),
    path('panier/ajouter/<int:product_id>/', views.cart_add, name='cart_add'),
    path('panier/modifier/<int:product_id>/', views.cart_update, name='cart_update'),
    path('panier/retirer/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('panier/vider/', views.cart_clear, name='cart_clear'),
    path('commander/', views.checkout, name='checkout'),
    path('commandes/', views.order_list, name='order_list'),
    path('commandes/gestion/', views.admin_order_list, name='admin_order_list'),
    path('commande/<uuid:reference>/', views.order_detail, name='order_detail'),
    path('commande/<uuid:reference>/payer/', views.order_pay, name='order_pay'),
    path('commande/<uuid:reference>/statut/', views.order_status_update, name='order_status_update'),
    path('commande/<uuid:reference>/paiement/retour/', views.payment_return, name='payment_return'),
    path('paiement/notification/', views.payment_notify, name='payment_notify'),
]
