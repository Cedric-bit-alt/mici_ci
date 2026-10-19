"""Intégration CinetPay (API REST v1 : https://api.cinetpay.co / sandbox https://api.cinetpay.net)."""
import logging
import secrets
from urllib.parse import quote

import requests
from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone

from .models import Order

logger = logging.getLogger(__name__)

BASE_URLS = {
    'production': 'https://api.cinetpay.co',
    'sandbox': 'https://api.cinetpay.net',
}
TIMEOUT = 15
AUTH_ERRORS = {'INVALID_CREDENTIALS', 'INVALID_TOKEN', 'EXPIRED_TOKEN'}
FAILED_STATUSES = {
    'FAILED', 'EXPIRED', 'INSUFFICIENT_BALANCE', 'NOT_ALLOWED',
    'USER_IS_BLOCKED', 'USER_NOT_FOUND', 'OTP_ERROR', 'OTP_EXPIRED',
}
IN_PROGRESS_STATUSES = {'INITIATED', 'PENDING'}


class PaymentError(Exception):
    """Erreur affichable à l'utilisateur ; le détail technique est journalisé."""


def is_configured():
    return bool(settings.CINETPAY_API_KEY and settings.CINETPAY_API_PASSWORD)


def _call(method, path, payload=None, token=None):
    url = BASE_URLS.get(settings.CINETPAY_ENV, BASE_URLS['sandbox']) + path
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        response = requests.request(method, url, json=payload, headers=headers, timeout=TIMEOUT)
        data = response.json() if response.content else {}
    except (requests.RequestException, ValueError) as exc:
        logger.exception('CinetPay %s %s a échoué', method, path)
        raise PaymentError('Le service de paiement est indisponible. Réessayez dans quelques instants.') from exc
    if not isinstance(data, dict):
        raise PaymentError('Réponse inattendue du service de paiement.')
    return response.status_code, data


def _get_token(force_refresh=False):
    cache_key = f'cinetpay:token:{settings.CINETPAY_ENV}:{settings.CINETPAY_API_KEY}'
    token = None if force_refresh else cache.get(cache_key)
    if token:
        return token

    status_code, data = _call('POST', '/v1/oauth/login', {
        'api_key': settings.CINETPAY_API_KEY,
        'api_password': settings.CINETPAY_API_PASSWORD,
    })
    nested = data.get('data') if isinstance(data.get('data'), dict) else {}
    token = data.get('access_token') or nested.get('token')
    if status_code >= 300 or not token:
        logger.error('Authentification CinetPay refusée : %s', data.get('status') or status_code)
        raise PaymentError('Le service de paiement est mal configuré. Contactez l\'administrateur.')

    expires_in = int(data.get('expires_in') or nested.get('expires_in') or 300)
    cache.set(cache_key, token, max(expires_in - 30, 30))
    return token


def _api(method, path, payload=None):
    status_code, data = _call(method, path, payload, _get_token())
    if status_code == 401 or data.get('status') in AUTH_ERRORS:
        status_code, data = _call(method, path, payload, _get_token(force_refresh=True))
    if not 200 <= status_code < 300:
        logger.error('CinetPay %s %s -> HTTP %s : %s', method, path, status_code, data)
        raise PaymentError('Le paiement n\'a pas pu être initialisé. Réessayez plus tard.')
    return data


def start_payment(order, request):
    """Crée une transaction CinetPay pour la commande et retourne l'URL du guichet de paiement."""
    if not is_configured():
        raise PaymentError('Le paiement en ligne n\'est pas encore activé sur ce site.')
    if order.total != order.total.to_integral_value():
        raise PaymentError('Le montant doit être un nombre entier pour être payé via CinetPay.')

    merchant_transaction_id = f'MICI{order.id}-{secrets.token_hex(6)}'
    return_url = request.build_absolute_uri(reverse('shop:payment_return', args=[order.reference]))
    data = _api('POST', '/v1/payment', {
        'currency': settings.CINETPAY_CURRENCY,
        'merchant_transaction_id': merchant_transaction_id,
        'amount': int(order.total),
        'success_url': return_url,
        'failed_url': return_url,
        'notify_url': request.build_absolute_uri(reverse('shop:payment_notify')),
        'lang': 'fr',
        'designation': f'Commande MICI n°{order.id}',
        'client_first_name': order.first_name,
        'client_last_name': order.last_name,
        'client_email': order.email,
    })

    payment_url = data.get('payment_url') or ''
    if not payment_url.startswith('https://'):
        logger.error('CinetPay n\'a pas renvoyé d\'URL de paiement : %s', data)
        raise PaymentError('Le paiement n\'a pas pu être initialisé. Réessayez plus tard.')

    order.merchant_transaction_id = merchant_transaction_id
    order.cinetpay_transaction_id = str(data.get('transaction_id') or '')
    order.notify_token = str(data.get('notify_token') or '')
    order.payment_url = payment_url
    order.status = Order.PENDING
    order.save(update_fields=[
        'merchant_transaction_id', 'cinetpay_transaction_id', 'notify_token',
        'payment_url', 'status', 'updated_at',
    ])
    return payment_url


def sync_payment(order):
    """Interroge CinetPay (seule source fiable) et met à jour le statut de la commande."""
    if not order.merchant_transaction_id or not is_configured():
        return None

    merchant_transaction_id = order.merchant_transaction_id
    data = _api('GET', f'/v1/payment/{quote(merchant_transaction_id, safe="")}')
    if data.get('merchant_transaction_id') != merchant_transaction_id:
        logger.error('Réponse CinetPay incohérente pour %s : %s', merchant_transaction_id, data)
        raise PaymentError('Impossible de vérifier le paiement.')

    remote_status = data.get('status')
    if remote_status == 'SUCCESS':
        Order.objects.filter(pk=order.pk, status__in=Order.PAYABLE_STATUSES).update(
            status=Order.PAID, paid_at=timezone.now(), updated_at=timezone.now(),
        )
    elif remote_status in FAILED_STATUSES:
        Order.objects.filter(
            pk=order.pk, status=Order.PENDING, merchant_transaction_id=merchant_transaction_id,
        ).update(status=Order.FAILED, updated_at=timezone.now())

    order.refresh_from_db()
    return remote_status
