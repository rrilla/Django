# Generated by Django 3.1.3 on 2020-11-27 03:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('idx', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=500)),
                ('point', models.IntegerField(default=0)),
                ('content', models.TextField()),
            ],
        ),
    ]
