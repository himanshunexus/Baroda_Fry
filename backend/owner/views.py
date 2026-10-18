from datetime import datetime, time, timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import Coalesce, TruncDate
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from store.models import Dish, Order, OrderItem
from store.serializers import DishSerializer, OrderSerializer
from .models import KitchenStaffRoster, RestaurantSettings


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active and request.user.is_superuser)


def control_data(settings):
    return {'is_store_open': settings.is_store_open, 'is_ordering_paused': settings.is_ordering_paused,
            'max_active_order_capacity': settings.max_active_order_capacity, 'updated_at': settings.updated_at}


def publish(group, event):
    import logging
    try:
        async_to_sync(get_channel_layer().group_send)(group, {'type': event})
    except Exception:
        logging.getLogger(__name__).exception('Committed change; WebSocket publish failed. Clients will poll.')


def period_bounds(period):
    now = timezone.now()
    today = timezone.localdate()
    if period == 'TODAY':
        start = today
        end = today + timedelta(days=1)
        previous_start = today - timedelta(days=1)
    elif period == 'THIS_WEEK':
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=7)
        previous_start = start - timedelta(days=7)
    elif period == 'THIS_MONTH':
        start = today.replace(day=1)
        end = (start.replace(year=start.year + 1, month=1) if start.month == 12 else start.replace(month=start.month + 1))
        previous_start = (start - timedelta(days=1)).replace(day=1)
    elif period == 'ALL_TIME':
        return None, None, None, now
    else:
        raise ValidationError({'period': 'Choose TODAY, THIS_WEEK, THIS_MONTH, or ALL_TIME.'})
    local = timezone.get_current_timezone()
    return (timezone.make_aware(datetime.combine(start, time.min), local),
            timezone.make_aware(datetime.combine(end, time.min), local),
            timezone.make_aware(datetime.combine(previous_start, time.min), local), now)


def sales_summary(query):
    # Cash orders count as completed order value, not verified collected payments.
    completed = query.filter(status=Order.Status.COMPLETED)
    values = completed.aggregate(orders=Count('id'), revenue=Coalesce(Sum('total_amount_paise'), 0),
                                 subsidies=Coalesce(Sum('delivery_subsidy_paise'), 0),
                                 offers=Coalesce(Sum('offer_discount_paise'), 0))
    return {'total_orders': values['orders'], 'revenue_paise': values['revenue'],
            'aov_paise': values['revenue'] // values['orders'] if values['orders'] else 0,
            'net_contribution_paise': values['revenue'] - values['subsidies'] - values['offers']}


class StoreStatusView(APIView):
    def get(self, request):
        return Response(control_data(RestaurantSettings.objects.get(pk=1)))


class OwnerOverviewView(APIView):
    permission_classes = [IsOwner]
    def get(self, request):
        period = request.query_params.get('period', 'TODAY')
        demo = request.query_params.get('demo', 'false').lower() == 'true'
        start, end, previous_start, now = period_bounds(period)
        all_orders = Order.objects.filter(is_demo=demo)
        scoped = all_orders.filter(created_at__gte=start, created_at__lt=end) if start else all_orders
        sales = all_orders.filter(status='COMPLETED', completed_at__gte=start, completed_at__lt=end) if start else all_orders.filter(status='COMPLETED')
        previous = all_orders.filter(status='COMPLETED', completed_at__gte=previous_start, completed_at__lt=start) if previous_start else all_orders.none()
        live = Order.objects.filter(is_demo=False).exclude(status__in=[Order.Status.COMPLETED, Order.Status.CANCELLED]).prefetch_related('items')
        counts = live.aggregate(pending=Count('id', filter=Q(status__in=['PAID', 'PENDING'])),
                                preparing=Count('id', filter=Q(status__in=['ACCEPTED', 'PREPARING'])),
                                delivery=Count('id', filter=Q(status='DISPATCHED')),
                                pickup=Count('id', filter=Q(status='READY', fulfilment_mode='PICKUP')),
                                ready=Count('id', filter=Q(status='READY')),
                                value=Coalesce(Sum('total_amount_paise'), 0))
        durations = scoped.aggregate(prep=Avg(F('ready_at') - F('accepted_at'), filter=Q(ready_at__isnull=False, accepted_at__isnull=False)),
                                     acceptance=Avg(F('accepted_at') - F('created_at'), filter=Q(accepted_at__isnull=False)))
        cancellations = scoped.filter(status='CANCELLED')
        cancelled_count = cancellations.count()
        order_count = scoped.count()
        chart = list(sales.annotate(day=TruncDate('completed_at')).values('day').annotate(
            orders=Count('id'), revenue_paise=Coalesce(Sum('total_amount_paise'), 0)).order_by('day'))
        return Response({'period': period, 'demo': demo, 'sales': sales_summary(sales), 'previous_sales': sales_summary(previous),
                         'live': {'count': live.count(), 'total_value_paise': counts['value'], 'pending': counts['pending'],
                                  'preparing': counts['preparing'], 'out_for_delivery': counts['delivery'],
                                  'ready_for_pickup': counts['pickup'], 'ready': counts['ready'],
                                  'orders': OrderSerializer(live, many=True).data},
                         'performance': {'average_prep_minutes': round(durations['prep'].total_seconds() / 60, 1) if durations['prep'] else None,
                                         'acceptance_delay_minutes': round(durations['acceptance'].total_seconds() / 60, 1) if durations['acceptance'] else None,
                                         'cancellation_rate_percent': round(100 * cancelled_count / order_count, 1) if order_count else 0,
                                         'cancelled_orders': cancelled_count, 'completed_orders': sales.count(),
                                         'cancellation_reasons': list(cancellations.values('cancellation_reason').annotate(count=Count('id')).order_by('-count'))},
                         'active_staff': KitchenStaffRoster.objects.filter(is_on_shift=True).count(),
                         'settings': control_data(RestaurantSettings.objects.get(pk=1)), 'chart': chart,
                         'generated_at': now})


@method_decorator(csrf_protect, name='dispatch')
class StoreControlView(APIView):
    permission_classes = [IsOwner]
    def post(self, request):
        allowed = {'is_store_open', 'is_ordering_paused', 'max_active_order_capacity'}
        if not request.data or not set(request.data).issubset(allowed):
            raise ValidationError('Provide only store status, pause, or capacity fields.')
        for field in ('is_store_open', 'is_ordering_paused'):
            if field in request.data and not isinstance(request.data[field], bool):
                raise ValidationError({field: 'Expected a boolean.'})
        if 'max_active_order_capacity' in request.data:
            capacity = request.data['max_active_order_capacity']
            if type(capacity) is not int or not 1 <= capacity <= 500:
                raise ValidationError({'max_active_order_capacity': 'Choose 1–500.'})
        with transaction.atomic():
            control = RestaurantSettings.objects.select_for_update().get(pk=1)
            for field, value in request.data.items(): setattr(control, field, value)
            control.save()
            transaction.on_commit(lambda: publish('store_status', 'store.changed'))
        return Response(control_data(control))


@method_decorator(csrf_protect, name='dispatch')
class MenuStockView(APIView):
    permission_classes = [IsOwner]
    def patch(self, request, dish_id):
        value = request.data.get('is_available')
        if not isinstance(value, bool): raise ValidationError({'is_available': 'Expected a boolean.'})
        with transaction.atomic():
            dish = Dish.objects.select_for_update().filter(pk=dish_id).first()
            if not dish: raise NotFound()
            dish.is_available = value
            dish.save(update_fields=['is_available'])
            transaction.on_commit(lambda: publish('store_status', 'store.changed'))
        return Response(DishSerializer(dish).data)


class TopDishesView(APIView):
    permission_classes = [IsOwner]
    def get(self, request):
        start, end, _, _ = period_bounds(request.query_params.get('period', 'TODAY'))
        demo = request.query_params.get('demo', 'false').lower() == 'true'
        lines = OrderItem.objects.filter(order__status='COMPLETED', order__is_demo=demo)
        if start: lines = lines.filter(order__completed_at__gte=start, order__completed_at__lt=end)
        rows = lines.values('dish_name', 'portion_label').annotate(units_sold=Coalesce(Sum('quantity'), 0),
                    gross_value_paise=Coalesce(Sum(F('quantity') * F('unit_price_paise')), 0)).order_by('-units_sold', '-gross_value_paise')[:5]
        images = {(dish.name, dish.portion_label): dish.image_cloudinary_url for dish in Dish.objects.all()}
        return Response([{**row, 'quantity': row['units_sold'],
                          'image_cloudinary_url': images.get((row['dish_name'], row['portion_label']), '')} for row in rows])


@method_decorator(csrf_protect, name='dispatch')
class RosterView(APIView):
    permission_classes = [IsOwner]
    def get(self, request):
        rows = [{'id': row.id, 'user_id': row.user_id, 'name': row.user.get_full_name() or row.user.username,
                          'role': row.role, 'is_on_shift': row.is_on_shift, 'clock_in_time': row.clock_in_time}
                         for row in KitchenStaffRoster.objects.select_related('user').order_by('role', 'user__username')]
        available = [{'id': user.pk, 'name': user.get_full_name() or user.username}
                     for user in get_user_model().objects.filter(is_staff=True, is_active=True, is_superuser=False).exclude(
                         pk__in=[row['user_id'] for row in rows]).order_by('username')]
        return Response({'roster': rows, 'available_staff': available})

    def post(self, request):
        user = get_user_model().objects.filter(pk=request.data.get('user_id'), is_staff=True, is_active=True).first()
        role = request.data.get('role')
        if not user or role not in KitchenStaffRoster.Role.values:
            raise ValidationError('Select an active staff account and a valid kitchen role.')
        row, created = KitchenStaffRoster.objects.get_or_create(user=user, defaults={'role': role})
        if not created:
            row.role = role
            row.save(update_fields=['role'])
        return Response({'id': row.id, 'user_id': user.pk, 'name': user.get_full_name() or user.username,
                         'role': row.role, 'is_on_shift': row.is_on_shift, 'clock_in_time': row.clock_in_time})


@method_decorator(csrf_protect, name='dispatch')
class RosterShiftView(APIView):
    permission_classes = [IsOwner]
    def patch(self, request, pk):
        value = request.data.get('is_on_shift')
        if not isinstance(value, bool): raise ValidationError({'is_on_shift': 'Expected a boolean.'})
        with transaction.atomic():
            row = KitchenStaffRoster.objects.select_for_update().filter(pk=pk).first()
            if not row: raise NotFound()
            row.is_on_shift = value
            row.clock_in_time = timezone.now() if value and not row.clock_in_time else (None if not value else row.clock_in_time)
            row.save(update_fields=['is_on_shift', 'clock_in_time'])
            transaction.on_commit(lambda: publish('kitchen', 'order.changed'))
        return Response({'id': row.id, 'is_on_shift': row.is_on_shift, 'clock_in_time': row.clock_in_time})
