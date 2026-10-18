from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Order
class OrderConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        pk = self.scope['url_route']['kwargs'].get('order_id')
        staff = self.scope['user'].is_authenticated and self.scope['user'].is_staff
        allowed = staff
        if pk and not staff:
            allowed = await database_sync_to_async(Order.objects.filter(pk=pk, owner_session=self.scope['session'].session_key or '').exists)()
        if not allowed: return await self.close(code=4403)
        self.group = f'order_{pk}' if pk else 'kitchen'
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({'type':'connected'})
    async def disconnect(self, code):
        if hasattr(self, 'group'): await self.channel_layer.group_discard(self.group, self.channel_name)
    async def order_changed(self, event):
        await self.send_json({'type':'order.changed', 'order_id':event['order_id']})


class StoreConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.group = 'store_status'
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected'})

    async def disconnect(self, code):
        if hasattr(self, 'group'):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def store_changed(self, event):
        await self.send_json({'type': 'store.changed'})
