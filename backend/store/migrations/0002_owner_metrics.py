from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('store', '0001_initial')]
    operations = [
        migrations.AddField(model_name='order', name='ready_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='order', name='cancellation_reason', field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(model_name='order', name='delivery_subsidy_paise', field=models.PositiveIntegerField(default=0)),
        migrations.AddField(model_name='order', name='offer_discount_paise', field=models.PositiveIntegerField(default=0)),
    ]
