import json
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Order, Product


class ShopTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Chapelet en bois', description='Bois d\'olivier', price=Decimal('2500'))
        self.other = Product.objects.create(name='Croix murale', description='Métal', price=Decimal('1250.50'))

    def test_visitor_sees_shop(self):
        response = self.client.get(reverse('shop:product_list'))
        self.assertContains(response, 'Chapelet en bois')

    def test_visitor_cannot_create_product(self):
        response = self.client.get(reverse('shop:product_create'))
        self.assertEqual(response.status_code, 302)

    def test_member_cannot_create_product(self):
        get_user_model().objects.create_user('membre', password='pass12345')
        self.client.login(username='membre', password='pass12345')
        response = self.client.post(reverse('shop:product_create'), {'name': 'X', 'price': '10', 'description': 'X'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(name='X').exists())

    def test_admin_can_create_product(self):
        get_user_model().objects.create_user('chef', password='pass12345', role='Admin')
        self.client.login(username='chef', password='pass12345')
        self.client.post(reverse('shop:product_create'), {
            'name': 'Médaille', 'price': '3000', 'description': 'Argent', 'available': 'on',
        })
        self.assertTrue(Product.objects.filter(name='Médaille', price=Decimal('3000')).exists())

    def test_cart_increments_and_totals(self):
        self.client.post(reverse('shop:cart_add', args=[self.product.id]))
        self.client.post(reverse('shop:cart_add', args=[self.product.id]))
        self.client.post(reverse('shop:cart_add', args=[self.other.id]), {'quantity': 2})

        response = self.client.get(reverse('shop:cart_detail'))
        self.assertEqual(response.context['total'], Decimal('7501.00'))
        self.assertEqual(response.context['cart_count'], 4)

    def test_cart_update_and_remove(self):
        self.client.post(reverse('shop:cart_add', args=[self.product.id]), {'quantity': 3})
        self.client.post(reverse('shop:cart_update', args=[self.product.id]), {'quantity': 1})
        self.assertEqual(self.client.get(reverse('shop:cart_detail')).context['total'], Decimal('2500'))

        self.client.post(reverse('shop:cart_remove', args=[self.product.id]))
        self.assertEqual(self.client.get(reverse('shop:cart_detail')).context['items'], [])

    def test_unavailable_product_cannot_be_added(self):
        self.product.available = False
        self.product.save()
        response = self.client.post(reverse('shop:cart_add', args=[self.product.id]))
        self.assertEqual(response.status_code, 404)

    def test_external_next_url_is_ignored(self):
        response = self.client.post(reverse('shop:cart_add', args=[self.product.id]), {'next': 'https://evil.example'})
        self.assertRedirects(response, reverse('shop:cart_detail'))

    def test_member_cannot_access_admin_orders(self):
        get_user_model().objects.create_user('membre', password='pass12345')
        self.client.login(username='membre', password='pass12345')
        self.assertEqual(self.client.get(reverse('shop:admin_order_list')).status_code, 302)

    def test_admin_price_must_be_integer_in_fcfa(self):
        get_user_model().objects.create_user('chef', password='pass12345', role='Admin')
        self.client.login(username='chef', password='pass12345')
        self.client.post(reverse('shop:product_create'), {'name': 'Bougie', 'price': '99.50', 'description': 'Cire'})
        self.assertFalse(Product.objects.filter(name='Bougie').exists())

    def test_admin_does_not_see_customer_menu_or_cart_buttons(self):
        get_user_model().objects.create_user('chef', password='pass12345', role='Admin')
        self.client.login(username='chef', password='pass12345')
        for url in (reverse('shop:product_list'), self.product.get_absolute_url()):
            response = self.client.get(url)
            self.assertNotContains(response, reverse('shop:cart_detail'))
            self.assertNotContains(response, reverse('shop:order_list') + '"')
            self.assertNotContains(response, reverse('shop:cart_add', args=[self.product.id]))
            self.assertContains(response, reverse('shop:admin_order_list'))

    def test_visitor_sees_cart_buttons(self):
        response = self.client.get(reverse('shop:product_list'))
        self.assertContains(response, reverse('shop:cart_detail'))
        self.assertContains(response, reverse('shop:cart_add', args=[self.product.id]))


CHECKOUT_DATA = {
    'first_name': 'Jean', 'last_name': 'Kouassi', 'email': 'jean@example.com',
    'phone': '+2250700000000', 'address': 'Rue 12', 'city': 'Abidjan',
}
CINETPAY_SETTINGS = {'CINETPAY_API_KEY': 'key', 'CINETPAY_API_PASSWORD': 'secret'}


@override_settings(**CINETPAY_SETTINGS)
class CheckoutTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name='Chapelet', description='Bois', price=Decimal('2500'))
        self.user = get_user_model().objects.create_user('client', password='pass12345', email='c@example.com')

    def _fill_cart(self, quantity=2):
        self.client.post(reverse('shop:cart_add', args=[self.product.id]), {'quantity': quantity})

    def _place_order(self, api_response=None):
        self.client.login(username='client', password='pass12345')
        self._fill_cart()
        api_response = api_response or {
            'payment_url': 'https://checkout.cinetpay.co/pay/abc',
            'transaction_id': 'cp-1', 'notify_token': 'nt-secret',
        }
        with mock.patch('shop.payments._api', return_value=api_response) as api:
            response = self.client.post(reverse('shop:checkout'), CHECKOUT_DATA)
        return response, api

    def test_checkout_requires_login(self):
        self._fill_cart()
        response = self.client.get(reverse('shop:checkout'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('shop:checkout')}")

    def test_login_redirects_back_to_checkout(self):
        response = self.client.post(
            f"{reverse('accounts:login')}?next={reverse('shop:checkout')}",
            {'username': 'client', 'password': 'pass12345'},
        )
        self.assertEqual(response.url, reverse('shop:checkout'))

    def test_checkout_creates_order_and_redirects_to_cinetpay(self):
        response, api = self._place_order()

        order = Order.objects.get()
        self.assertRedirects(response, 'https://checkout.cinetpay.co/pay/abc', fetch_redirect_response=False)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total, Decimal('5000'))
        self.assertEqual(order.items.get().quantity, 2)
        self.assertEqual(order.status, Order.PENDING)
        self.assertEqual(order.notify_token, 'nt-secret')

        method, path, payload = api.call_args.args
        self.assertEqual((method, path), ('POST', '/v1/payment'))
        self.assertEqual(payload['amount'], 5000)
        self.assertEqual(payload['currency'], 'XOF')
        self.assertEqual(payload['merchant_transaction_id'], order.merchant_transaction_id)
        self.assertLessEqual(len(order.merchant_transaction_id), 30)
        self.assertEqual(self.client.get(reverse('shop:cart_detail')).context['items'], [])

    @override_settings(CINETPAY_API_KEY='')
    def test_checkout_without_cinetpay_config_keeps_order(self):
        self.client.login(username='client', password='pass12345')
        self._fill_cart()
        response = self.client.post(reverse('shop:checkout'), CHECKOUT_DATA)
        order = Order.objects.get()
        self.assertRedirects(response, order.get_absolute_url())
        self.assertEqual(order.status, Order.PENDING)

    def _notify(self, order, token):
        return self.client.post(
            reverse('shop:payment_notify'),
            json.dumps({'notify_token': token, 'merchant_transaction_id': order.merchant_transaction_id, 'transaction_id': 'cp-1'}),
            content_type='application/json',
        )

    def test_webhook_with_bad_token_is_rejected(self):
        self._place_order()
        order = Order.objects.get()
        with mock.patch('shop.payments._api') as api:
            response = self._notify(order, 'wrong')
        self.assertEqual(response.status_code, 403)
        api.assert_not_called()
        order.refresh_from_db()
        self.assertEqual(order.status, Order.PENDING)

    def test_webhook_marks_order_paid_only_after_api_check(self):
        self._place_order()
        order = Order.objects.get()
        status = {'status': 'SUCCESS', 'merchant_transaction_id': order.merchant_transaction_id}
        with mock.patch('shop.payments._api', return_value=status) as api:
            response = self._notify(order, 'nt-secret')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(api.call_args.args[:2], ('GET', f'/v1/payment/{order.merchant_transaction_id}'))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.PAID)
        self.assertIsNotNone(order.paid_at)

    def test_payment_return_marks_failed(self):
        self._place_order()
        order = Order.objects.get()
        status = {'status': 'FAILED', 'merchant_transaction_id': order.merchant_transaction_id}
        with mock.patch('shop.payments._api', return_value=status):
            response = self.client.get(reverse('shop:payment_return', args=[order.reference]))
        self.assertRedirects(response, order.get_absolute_url())
        order.refresh_from_db()
        self.assertEqual(order.status, Order.FAILED)

    def test_other_user_cannot_see_order(self):
        self._place_order()
        order = Order.objects.get()
        get_user_model().objects.create_user('autre', password='pass12345')
        self.client.login(username='autre', password='pass12345')
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)
        self.assertEqual(self.client.post(reverse('shop:order_pay', args=[order.reference])).status_code, 404)

    def test_admin_can_update_status(self):
        self._place_order()
        order = Order.objects.get()
        get_user_model().objects.create_user('chef', password='pass12345', role='Admin')
        self.client.login(username='chef', password='pass12345')
        self.assertEqual(self.client.get(reverse('shop:admin_order_list')).status_code, 200)
        self.client.post(reverse('shop:order_status_update', args=[order.reference]), {'status': Order.SHIPPED})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.SHIPPED)


@override_settings(**CINETPAY_SETTINGS, CINETPAY_ENV='production')
class CinetPayClientTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    @staticmethod
    def _response(status_code, data):
        response = mock.Mock(status_code=status_code, content=b'1')
        response.json.return_value = data
        return response

    def test_bearer_token_is_fetched_and_refreshed_once(self):
        from . import payments
        responses = [
            self._response(200, {'access_token': 'old', 'expires_in': 3600}),
            self._response(401, {'status': 'EXPIRED_TOKEN'}),
            self._response(200, {'access_token': 'new', 'expires_in': 3600}),
            self._response(200, {'status': 'SUCCESS'}),
        ]
        with mock.patch('shop.payments.requests.request', side_effect=responses) as request:
            self.assertEqual(payments._api('GET', '/v1/payment/X'), {'status': 'SUCCESS'})

        calls = request.call_args_list
        self.assertEqual(calls[0].args, ('POST', 'https://api.cinetpay.co/v1/oauth/login'))
        self.assertEqual(calls[0].kwargs['json'], {'api_key': 'key', 'api_password': 'secret'})
        self.assertEqual(calls[1].kwargs['headers']['Authorization'], 'Bearer old')
        self.assertEqual(calls[3].kwargs['headers']['Authorization'], 'Bearer new')
