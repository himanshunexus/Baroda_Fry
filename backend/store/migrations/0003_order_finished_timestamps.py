from django.db import migrations, models


def backfill_timestamps(apps, schema_editor):
    from django.db.models import F
    Order = apps.get_model('store', 'Order')
    Order.objects.filter(status='COMPLETED', completed_at__isnull=True).update(completed_at=F('created_at'))
    Order.objects.filter(status='CANCELLED', cancelled_at__isnull=True).update(cancelled_at=F('created_at'))


class Migration(migrations.Migration):
    dependencies = [('store', '0002_owner_metrics')]
    operations = [
        migrations.AddField(model_name='order', name='completed_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='order', name='cancelled_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.RunPython(backfill_timestamps, migrations.RunPython.noop),
    ]
