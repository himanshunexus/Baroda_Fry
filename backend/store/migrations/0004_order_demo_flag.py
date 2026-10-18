from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('store', '0003_order_finished_timestamps')]
    operations = [
        migrations.AddField(model_name='order', name='is_demo', field=models.BooleanField(db_index=True, default=False, editable=False)),
    ]
