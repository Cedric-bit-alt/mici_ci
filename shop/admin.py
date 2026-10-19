from django.contrib import admin

from .models import Order, OrderItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'available', 'created_at')
    list_filter = ('available', 'created_at')
    list_editable = ('price', 'available')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name', 'price', 'quantity')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'last_name', 'first_name', 'total', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'merchant_transaction_id')
    readonly_fields = (
        'reference', 'user', 'total', 'merchant_transaction_id', 'cinetpay_transaction_id',
        'created_at', 'updated_at', 'paid_at',
    )
    inlines = [OrderItemInline]
