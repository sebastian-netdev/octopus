# Generated by Django 4.2.7 on 2023-11-11 11:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('SellAssist', '0002_alter_sellassistproduct_ean'),
    ]

    operations = [
        migrations.CreateModel(
            name='SellAssistProductRegistered',
            fields=[
                ('sellassistproduct_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='SellAssist.sellassistproduct')),
            ],
            bases=('SellAssist.sellassistproduct',),
        ),
    ]