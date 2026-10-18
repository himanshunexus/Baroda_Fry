import socket
from django.conf import settings

def safe(text):
    return ''.join(c for c in str(text) if c.isprintable()).encode('ascii', 'replace')

def format_ticket(order):
    lines = [b'\x1b@\x1ba\x01', b'BARODA FRY CENTRE\n', safe(order.order_number)+b'\n', safe(order.fulfilment_mode)+b'\n', b'\x1ba\x00', b'-'*32+b'\n']
    for item in order.items.all():
        lines += [safe(f'{item.quantity} x {item.dish_name}')+b'\n', safe(item.portion_label)+b'\n', safe(item.customization_notes)+b'\n']
    lines += [b'-'*32+b'\n', safe(order.customer_name)+b'\n', b'PAYMENT: UNPAID / CASH\n\n\n', b'\x1dV\x00']
    return b''.join(lines)

def send_ticket(payload):
    if not settings.PRINTER_HOST: raise RuntimeError('PRINTER_HOST is not configured')
    with socket.create_connection((settings.PRINTER_HOST, settings.PRINTER_PORT), timeout=5) as printer:
        printer.sendall(payload)
