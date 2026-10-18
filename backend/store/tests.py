import uuid
import os
from io import StringIO
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core.management import call_command
from rest_framework.test import APIClient
from .models import Dish, Order
from .kitchen_printer import format_ticket

class OrderingTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

        self.client = APIClient(enforce_csrf_checks=True)
        self.csrf = self.client.get('/api/session').data['csrfToken']
        self.dish = Dish.objects.create(name='Tikka',category='Starters',price_paise=12345,stock_quantity=2,portion_label='Full',spice_choices_supported=['Hot'])
        self.payload = dict(customer_name='Test Guest',customer_phone='9876543210',fulfilment_mode='PICKUP',idempotency_key=str(uuid.uuid4()),items=[dict(dish_id=self.dish.pk,quantity=2,spice='Hot')],total_amount_paise=1)
    def post(self, payload=None): return self.client.post('/api/orders',payload or self.payload,format='json',HTTP_X_CSRFTOKEN=self.csrf)
    def test_server_prices_snapshots_and_idempotency(self):
        result=self.post();self.assertEqual(result.status_code,201)
        self.assertEqual(result.data['total_amount_paise'],25925)
        self.assertEqual(result.data['payment_status'],'UNPAID')
        self.dish.refresh_from_db();self.assertEqual(self.dish.stock_quantity,0)
        self.dish.price_paise=99999;self.dish.name='Changed';self.dish.save()
        item=Order.objects.get().items.get();self.assertEqual(item.unit_price_paise,12345);self.assertEqual(item.dish_name,'Tikka')
        self.assertEqual(self.post().status_code,200);self.assertEqual(Order.objects.count(),1)
    def test_stock_and_invalid_quantities(self):
        self.payload['items'][0]['quantity']=3
        self.assertEqual(self.post().status_code,400);self.assertEqual(Order.objects.count(),0)
        self.payload['items'][0]['quantity']=-1
        self.assertEqual(self.post().status_code,400)
    def test_delivery_zone_and_csrf(self):
        self.assertEqual(self.client.post('/api/orders',self.payload,format='json').status_code,403)
        self.payload.update(fulfilment_mode='DELIVERY',pincode='999999',delivery_address='Example street')
        self.assertEqual(self.post().status_code,400)
    def test_order_privacy_and_staff_permissions(self):
        result=self.post();pk=result.data['id']
        other=APIClient();self.assertEqual(other.get(f'/api/orders/{pk}').status_code,404)
        self.assertEqual(self.client.get('/api/orders/active').status_code,403)
        self.assertEqual(self.client.put(f'/api/orders/{pk}/status',{'status':'ACCEPTED'},format='json',HTTP_X_CSRFTOKEN=self.csrf).status_code,403)
    def test_transition_and_cancel_restores_stock_once(self):
        pk=self.post().data['id']
        user=User.objects.create_user('chef',password='a-strong-test-password',is_staff=True)
        self.client.force_authenticate(user)
        url=f'/api/orders/{pk}/status'
        self.assertEqual(self.client.put(url,{'status':'READY'},format='json').status_code,400)
        self.assertEqual(self.client.put(url,{'status':'ACCEPTED'},format='json').status_code,200)
        self.assertIsNotNone(Order.objects.get().accepted_at)
        self.assertEqual(self.client.put(url,{'status':'CANCELLED'},format='json').status_code,200)
        self.assertEqual(self.client.put(url,{'status':'CANCELLED'},format='json').status_code,400)
        self.dish.refresh_from_db();self.assertEqual(self.dish.stock_quantity,2)
    def test_quote_does_not_reserve_stock(self):
        result=self.client.post('/api/orders/quote',self.payload,format='json',HTTP_X_CSRFTOKEN=self.csrf)
        self.assertEqual(result.status_code,200);self.assertEqual(Order.objects.count(),0)
        self.dish.refresh_from_db();self.assertEqual(self.dish.stock_quantity,2)
    def test_printer_sanitizes_control_codes(self):
        self.post();order=Order.objects.get();order.customer_name='Guest\x1b@'
        ticket=format_ticket(order)
        self.assertNotIn(b'Guest\x1b@',ticket)
        self.assertIn(b'PAYMENT: UNPAID',ticket)


class BootstrapTests(TestCase):
    def test_creates_admin_once_without_resetting_password(self):
        with patch.dict(os.environ, {
            'BOOTSTRAP_ADMIN_USERNAME': 'prototype_admin',
            'BOOTSTRAP_ADMIN_PASSWORD': 'long-random-test-password-92841',
            'BOOTSTRAP_SAMPLE_MENU': 'false',
        }):
            call_command('bootstrap', stdout=StringIO())
            admin = User.objects.get(username='prototype_admin')
            self.assertTrue(admin.is_superuser)
            self.assertTrue(admin.check_password('long-random-test-password-92841'))
            admin.set_password('changed-after-first-login-73652')
            admin.save()
            call_command('bootstrap', stdout=StringIO())
            admin.refresh_from_db()
            self.assertTrue(admin.check_password('changed-after-first-login-73652'))

    def test_seed_only_when_empty(self):
        with patch.dict(os.environ, clear=False):
            os.environ.pop('BOOTSTRAP_SAMPLE_MENU', None)
            call_command('bootstrap', stdout=StringIO())
            self.assertEqual(Dish.objects.count(), 12)
            Dish.objects.filter(name='Butter Chicken').update(price_paise=99999)
            call_command('bootstrap', stdout=StringIO())
            self.assertEqual(Dish.objects.get(name='Butter Chicken').price_paise, 99999)

    def test_sample_menu_can_be_disabled(self):
        with patch.dict(os.environ, {'BOOTSTRAP_SAMPLE_MENU': 'false'}, clear=False):
            call_command('bootstrap', stdout=StringIO())
            self.assertFalse(Dish.objects.exists())
