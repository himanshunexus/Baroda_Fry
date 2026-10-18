import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_settings(apps, schema_editor):
    apps.get_model('owner', 'RestaurantSettings').objects.get_or_create(pk=1)


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='RestaurantSettings', fields=[
            ('id', models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
            ('is_store_open', models.BooleanField(default=True)),
            ('is_ordering_paused', models.BooleanField(default=False)),
            ('max_active_order_capacity', models.PositiveIntegerField(default=15)),
            ('updated_at', models.DateTimeField(auto_now=True)),
        ]),
        migrations.CreateModel(name='KitchenStaffRoster', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('role', models.CharField(choices=[('HEAD_CHEF', 'Head Chef'), ('LINE_COOK', 'Line Cook'), ('PACKER', 'Packer / Dispatch')], max_length=20)),
            ('is_on_shift', models.BooleanField(default=False)),
            ('clock_in_time', models.DateTimeField(blank=True, null=True)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='kitchen_roster', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.RunPython(create_settings, migrations.RunPython.noop),
    ]
