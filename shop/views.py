import hmac
import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from . import payments
from .cart import Cart
from .forms import CartQuantityForm, CheckoutForm, OrderStatusForm, ProductForm
from .models import Order, OrderItem, Product


def admin_required(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_user():
            messages.error(request, 'Vous n\'avez pas accès à cette page.')
            return redirect('shop:product_list')
        return view(request, *args, **kwargs)
    return wrapper


def product_list(request):
    products = Product.objects.all()
    if not (request.user.is_authenticated and request.user.is_admin_user()):
        products = products.filter(available=True)

    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    page_obj = Paginator(products, 9).get_page(request.GET.get('page'))
    return render(request, 'shop/product_list.html', {'page_obj': page_obj, 'query': query})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if not product.available and not (request.user.is_authenticated and request.user.is_admin_user()):
        messages.error(request, 'Cet article n\'est plus disponible.')
        return redirect('shop:product_list')
    return render(request, 'shop/product_detail.html', {'product': product})


@admin_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Article ajouté à la boutique.')
            return redirect(product)
    else:
        form = ProductForm()
    return render(request, 'shop/product_form.html', {'form': form, 'title': 'Ajouter un article'})


@admin_required
def product_edit(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Article modifié avec succès.')
            return redirect(product)
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop/product_form.html', {
        'form': form, 'product': product, 'title': 'Modifier l\'article',
    })


@admin_required
def product_delete(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Article supprimé de la boutique.')
        return redirect('shop:product_list')
    return render(request, 'shop/product_confirm_delete.html', {'product': product})


def cart_detail(request):
    cart = Cart(request)
    items = cart.get_items()
    return render(request, 'shop/cart.html', {'items': items, 'total': cart.get_total(items)})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    form = CartQuantityForm(request.POST)
    quantity = form.cleaned_data['quantity'] if form.is_valid() else 1
    Cart(request).add(product, max(quantity, 1))
    messages.success(request, f'« {product.name} » a été ajouté à votre panier.')

    next_url = request.POST.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(next_url)
    return redirect('shop:cart_detail')


@require_POST
def cart_update(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = CartQuantityForm(request.POST)
    if form.is_valid():
        Cart(request).update(product, form.cleaned_data['quantity'])
    else:
        messages.error(request, 'Quantité invalide.')
    return redirect('shop:cart_detail')


@require_POST
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Cart(request).remove(product)
    messages.success(request, f'« {product.name} » a été retiré du panier.')
    return redirect('shop:cart_detail')


@require_POST
def cart_clear(request):
    Cart(request).clear()
    messages.success(request, 'Votre panier a été vidé.')
    return redirect('shop:cart_detail')


@login_required
def checkout(request):
    cart = Cart(request)
    items = cart.get_items()
    if not items:
        messages.info(request, 'Votre panier est vide.')
        return redirect('shop:cart_detail')
    total = cart.get_total(items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.total = total
                order.save()
                OrderItem.objects.bulk_create([
                    OrderItem(
                        order=order,
                        product=item['product'],
                        product_name=item['product'].name,
                        price=item['product'].price,
                        quantity=item['quantity'],
                    )
                    for item in items
                ])
            cart.clear()

            try:
                return redirect(payments.start_payment(order, request))
            except payments.PaymentError as exc:
                messages.warning(request, f'Commande n°{order.id} enregistrée, mais {exc}')
                return redirect(order)
    else:
        user = request.user
        form = CheckoutForm(initial={
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
        })

    return render(request, 'shop/checkout.html', {'form': form, 'items': items, 'total': total})


def _get_order_for(request, reference):
    order = get_object_or_404(Order.objects.prefetch_related('items'), reference=reference)
    if order.user_id != request.user.id and not request.user.is_admin_user():
        raise Http404
    return order


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    page_obj = Paginator(orders, 10).get_page(request.GET.get('page'))
    return render(request, 'shop/order_list.html', {'page_obj': page_obj, 'title': 'Mes commandes'})


@login_required
def order_detail(request, reference):
    order = _get_order_for(request, reference)
    context = {'order': order}
    if request.user.is_admin_user():
        context['status_form'] = OrderStatusForm(instance=order)
    return render(request, 'shop/order_detail.html', context)


@login_required
@require_POST
def order_pay(request, reference):
    order = _get_order_for(request, reference)
    if order.user_id != request.user.id:
        raise Http404
    if not order.is_payable:
        messages.info(request, 'Cette commande ne peut plus être payée.')
        return redirect(order)

    try:
        remote_status = payments.sync_payment(order)
        if order.status == Order.PAID:
            messages.success(request, 'Cette commande est déjà payée.')
            return redirect(order)
        # Évite un double paiement si une transaction est encore en cours
        if remote_status in payments.IN_PROGRESS_STATUSES and order.payment_url:
            return redirect(order.payment_url)
        return redirect(payments.start_payment(order, request))
    except payments.PaymentError as exc:
        messages.error(request, str(exc))
        return redirect(order)


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def payment_return(request, reference):
    """Retour du client depuis CinetPay (succès ou échec) : on vérifie auprès de l'API."""
    order = get_object_or_404(Order, reference=reference)
    try:
        payments.sync_payment(order)
    except payments.PaymentError:
        pass

    if order.status == Order.PAID:
        messages.success(request, 'Paiement confirmé. Merci pour votre commande !')
    elif order.status == Order.FAILED:
        messages.error(request, 'Le paiement a échoué ou a été annulé. Vous pouvez réessayer.')
    else:
        messages.info(request, 'Paiement en cours de vérification. Actualisez la page dans quelques instants.')
    return redirect(order)


@csrf_exempt
@require_POST
def payment_notify(request):
    """Webhook CinetPay : simple signal, le statut est toujours revérifié via l'API."""
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest()
    else:
        payload = request.POST.dict()
    if not isinstance(payload, dict):
        return HttpResponseBadRequest()

    merchant_transaction_id = str(payload.get('merchant_transaction_id') or '')
    notify_token = str(payload.get('notify_token') or '')
    order = Order.objects.filter(merchant_transaction_id=merchant_transaction_id).first() if merchant_transaction_id else None
    if order is None or not order.notify_token or not hmac.compare_digest(notify_token, order.notify_token):
        return HttpResponseForbidden()

    try:
        payments.sync_payment(order)
    except payments.PaymentError:
        return HttpResponse(status=503)
    return HttpResponse('OK')


@admin_required
def admin_order_list(request):
    orders = Order.objects.select_related('user')
    status = request.GET.get('status')
    if status in dict(Order.STATUS_CHOICES):
        orders = orders.filter(status=status)
    page_obj = Paginator(orders, 20).get_page(request.GET.get('page'))
    return render(request, 'shop/order_list.html', {
        'page_obj': page_obj,
        'title': 'Commandes clients',
        'admin_view': True,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status,
    })


@admin_required
@require_POST
def order_status_update(request, reference):
    order = get_object_or_404(Order, reference=reference)
    form = OrderStatusForm(request.POST, instance=order)
    if form.is_valid():
        form.save()
        messages.success(request, f'Statut de la commande n°{order.id} mis à jour.')
    else:
        messages.error(request, 'Statut invalide.')
    return redirect(order)
