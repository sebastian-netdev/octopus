# Generated by Django 4.2.7 on 2023-11-11 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KauflandAPI',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.CharField(max_length=200)),
                ('clientkey', models.CharField(max_length=200)),
                ('secretkey', models.CharField(max_length=200)),
                ('stock_synchro', models.CharField(choices=[('1h', '1h'), ('4h', '4h'), ('8h', '8h'), ('24', '24h')], default='4h', max_length=10)),
                ('price_synchro', models.CharField(choices=[('1h', '1h'), ('4h', '4h'), ('8h', '8h'), ('24', '24h')], default='4h', max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='KauflandAPICallLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateField(auto_now=True)),
                ('status_code', models.IntegerField()),
                ('has_error', models.BooleanField(default=False)),
                ('response', models.TextField()),
                ('method', models.CharField(max_length=200)),
            ],
        ),
    ]