from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0164_orderitem_color_orderitem_size_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='color',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='size',
        ),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(default='e09a5f7b80ff47e9bbb6e4bee5e9e334', max_length=50, unique=True),
        ),
    ]