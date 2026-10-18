import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError, call_command

from store.models import Dish


class Command(BaseCommand):
    help = 'One-time, environment-driven bootstrap for hosts without shell access.'

    def handle(self, *args, **options):
        username = os.getenv('BOOTSTRAP_ADMIN_USERNAME', '').strip()
        password = os.getenv('BOOTSTRAP_ADMIN_PASSWORD', '')
        if bool(username) != bool(password):
            raise CommandError('Set both BOOTSTRAP_ADMIN_USERNAME and BOOTSTRAP_ADMIN_PASSWORD, or neither.')

        if username:
            user_model = get_user_model()
            existing = user_model.objects.filter(username=username).first()
            if existing:
                if not existing.is_superuser or not existing.is_staff:
                    raise CommandError('Bootstrap username belongs to a non-admin account.')
                self.stdout.write('Bootstrap admin already exists; password left unchanged.')
            else:
                try:
                    validate_password(password)
                except ValidationError as exc:
                    raise CommandError('Bootstrap password does not pass Django password validation.') from exc
                user_model.objects.create_superuser(username=username, email='', password=password)
                self.stdout.write(self.style.SUCCESS('Bootstrap admin created.'))

        # The prototype ships with a sample catalog so a fresh database is usable
        # on hosts without a shell. Existing menus are never overwritten.
        if os.getenv('BOOTSTRAP_SAMPLE_MENU', 'true').lower() == 'true':
            if Dish.objects.exists():
                self.stdout.write('Menu already has dishes; sample seed skipped.')
            else:
                use_cloudinary = os.getenv('BOOTSTRAP_CLOUDINARY_IMAGES', 'false').lower() == 'true'
                if use_cloudinary and not os.getenv('CLOUDINARY_URL'):
                    raise CommandError('BOOTSTRAP_CLOUDINARY_IMAGES requires CLOUDINARY_URL.')
                call_command('seed_menu', cloudinary=use_cloudinary)
