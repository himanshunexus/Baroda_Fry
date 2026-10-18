import uuid
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import ValidationError, NotFound
from .models import Dish, Order, OrderItem
from .serializers import DishSerializer, OrderSerializer, CheckoutSerializer
from .services import price_cart, broadcast
from owner.models import RestaurantSettings

class SessionView(APIView):
    def get(self, request):
        if not request.session.session_key: request.session.create()
        return Response({'csrfToken':get_token(request), 'is_staff':request.user.is_staff})

@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    throttle_scope = 'login'
    def post(self, request):
        user = authenticate(request, username=request.data.get('username'), password=request.data.get('password'))
        if not user or not user.is_staff: return Response({'detail':'Invalid staff credentials.'}, status=403)
        login(request, user)
        return Response({'csrfToken':get_token(request), 'is_staff':True})
    def delete(self, request):
        logout(request)
        return Response({'ok':True})

class MenuView(APIView):
    def get(self, request):
        from django.conf import settings
        return Response({'dishes':DishSerializer(Dish.objects.all(), many=True).data, 'delivery_pincodes':settings.DELIVERY_PINCODES, 'sample_prices':True})

@method_decorator(csrf_protect, name='dispatch')
class CheckoutView(APIView):
    throttle_scope = 'checkout'
    def post(self, request, quote=False):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not request.session.session_key: request.session.create()
        with transaction.atomic():
            control = RestaurantSettings.objects.select_for_update().get(pk=1)
            if not control.is_store_open or control.is_ordering_paused:
                raise ValidationError('Ordering is temporarily paused. Please try again later.')
            # Lock the persistent session row to serialize retries with the same session.
            from django.contrib.sessions.models import Session
            Session.objects.select_for_update().get(session_key=request.session.session_key)
            previous = Order.objects.filter(idempotency_key=data['idempotency_key']).first()
            if previous and not quote:
                if previous.owner_session != request.session.session_key: raise ValidationError('Idempotency key already used.')
                return Response(OrderSerializer(previous).data)
            dishes, quantities, totals = price_cart(data, lock=True)
            if quote: return Response(totals)
            order = Order.objects.create(order_number='BFC-'+uuid.uuid4().hex[:12].upper(), owner_session=request.session.session_key, **totals, **{k:v for k,v in data.items() if k != 'items'})
            for line in data['items']:
                dish = dishes[line['dish_id']]
                OrderItem.objects.create(order=order, dish=dish, dish_name=dish.name, unit_price_paise=dish.price_paise, quantity=line['quantity'], portion_label=dish.portion_label, customization_notes=' · '.join(filter(None, [line['spice'],line['notes']])))
            for pk, qty in quantities.items():
                if dishes[pk].stock_quantity != -1: Dish.objects.filter(pk=pk).update(stock_quantity=F('stock_quantity')-qty)
            transaction.on_commit(lambda: broadcast(order.id))
        return Response(OrderSerializer(order).data, status=201)

class ActiveOrdersView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        return Response(OrderSerializer(Order.objects.exclude(status__in=['COMPLETED','CANCELLED']).prefetch_related('items'), many=True).data)

class OrderDetailView(APIView):
    def get(self, request, pk):
        query = Order.objects.all() if request.user.is_staff else Order.objects.filter(owner_session=request.session.session_key or '')
        order = query.filter(pk=pk).first()
        if not order: raise NotFound()
        return Response(OrderSerializer(order).data)

class OrderStatusView(APIView):
    permission_classes = [IsAdminUser]
    def put(self, request, pk):
        with transaction.atomic():
            order = Order.objects.select_for_update().filter(pk=pk).first()
            if not order: raise NotFound()
            target = request.data.get('status')
            if target == 'CANCELLED':
                reason = str(request.data.get('reason', '')).strip()[:120]
                if not reason: raise ValidationError('A cancellation reason is required.')
                order.cancellation_reason = reason
            try: order.transition(target)
            except DjangoValidationError as e: raise ValidationError(e.messages)
            if target == 'CANCELLED': order.save(update_fields=['cancellation_reason'])
            if target == 'CANCELLED':
                for item in order.items.order_by('dish_id'):
                    if item.dish_id: Dish.objects.filter(pk=item.dish_id, stock_quantity__gte=0).update(stock_quantity=F('stock_quantity')+item.quantity)
            transaction.on_commit(lambda: broadcast(order.id))
        return Response(OrderSerializer(order).data)

class PrintView(APIView):
    permission_classes = [IsAdminUser]
    throttle_scope = 'print'
    def post(self, request, pk):
        from django.conf import settings
        from .tasks import print_ticket
        if not Order.objects.filter(pk=pk).exists(): raise NotFound()
        if not settings.PRINTER_HOST: return Response({'detail':'Kitchen printer is not configured.'}, status=503)
        try: print_ticket.delay(str(pk))
        except Exception: return Response({'detail':'Print queue unavailable. Try again.'}, status=503)
        return Response({'detail':'Ticket queued.'}, status=202)
