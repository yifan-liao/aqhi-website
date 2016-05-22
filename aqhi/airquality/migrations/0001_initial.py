# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-11 07:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='City',
            fields=[
                ('name_en', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('name_cn', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='CityPrimaryPollutantItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pollutant', models.CharField(choices=[('co', 'CO/1h'), ('no2', 'NO2/1h'), ('o3', 'O3/1h'), ('o3_8b', 'O3/8h'), ('pm10', 'PM10/1h'), ('pm2_5', 'PM2.5/1h'), ('so2', 'SO2/1h')], max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='CityRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aqi', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('co', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('no2', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('o3', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('o3_8h', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('pm10', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('pm2_5', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('so2', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('quality', models.CharField(blank=True, choices=[('E', 'Excellent'), ('G', 'Good'), ('LP', 'Lightly Polluted'), ('MP', 'Moderately Polluted'), ('HP', 'Heavily Polluted'), ('SP', 'Severely Polluted')], max_length=2)),
                ('update_dtm', models.DateTimeField(db_index=True)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cities_airquality_cityrecord', to='airquality.City')),
            ],
        ),
        migrations.CreateModel(
            name='EstimatedCityPrimaryPollutantItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pollutant', models.CharField(choices=[('co', 'CO/1h'), ('no2', 'NO2/1h'), ('o3', 'O3/1h'), ('o3_8b', 'O3/8h'), ('pm10', 'PM10/1h'), ('pm2_5', 'PM2.5/1h'), ('so2', 'SO2/1h')], max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='EstimatedCityRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aqi', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('co', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('no2', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('o3', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('o3_8h', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('pm10', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('pm2_5', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('so2', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('quality', models.CharField(blank=True, choices=[('E', 'Excellent'), ('G', 'Good'), ('LP', 'Lightly Polluted'), ('MP', 'Moderately Polluted'), ('HP', 'Heavily Polluted'), ('SP', 'Severely Polluted')], max_length=2)),
                ('original_record', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='estimated_record', to='airquality.CityRecord')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EstimatedStationPrimaryPollutantItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pollutant', models.CharField(choices=[('co', 'CO/1h'), ('no2', 'NO2/1h'), ('o3', 'O3/1h'), ('o3_8b', 'O3/8h'), ('pm10', 'PM10/1h'), ('pm2_5', 'PM2.5/1h'), ('so2', 'SO2/1h')], max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='EstimatedStationRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aqi', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('co', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('no2', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('o3', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('o3_8h', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('pm10', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('pm2_5', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('so2', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('quality', models.CharField(blank=True, choices=[('E', 'Excellent'), ('G', 'Good'), ('LP', 'Lightly Polluted'), ('MP', 'Moderately Polluted'), ('HP', 'Heavily Polluted'), ('SP', 'Severely Polluted')], max_length=2)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_cn', models.CharField(max_length=50)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stations', related_query_name='station', to='airquality.City')),
            ],
        ),
        migrations.CreateModel(
            name='StationPrimaryPollutantItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pollutant', models.CharField(choices=[('co', 'CO/1h'), ('no2', 'NO2/1h'), ('o3', 'O3/1h'), ('o3_8b', 'O3/8h'), ('pm10', 'PM10/1h'), ('pm2_5', 'PM2.5/1h'), ('so2', 'SO2/1h')], max_length=5)),
            ],
        ),
        migrations.CreateModel(
            name='StationRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aqi', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('co', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('no2', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('o3', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('o3_8h', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('pm10', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('pm2_5', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('so2', models.DecimalField(blank=True, decimal_places=4, max_digits=8, null=True)),
                ('quality', models.CharField(blank=True, choices=[('E', 'Excellent'), ('G', 'Good'), ('LP', 'Lightly Polluted'), ('MP', 'Moderately Polluted'), ('HP', 'Heavily Polluted'), ('SP', 'Severely Polluted')], max_length=2)),
                ('city_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='station_records', to='airquality.CityRecord')),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stations_airquality_stationrecord', to='airquality.Station')),
            ],
        ),
        migrations.AddField(
            model_name='stationprimarypollutantitem',
            name='station_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primary_pollutants', related_query_name='primary_pollutant', to='airquality.StationRecord'),
        ),
        migrations.AddField(
            model_name='estimatedstationrecord',
            name='original_record',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='estimated_record', to='airquality.StationRecord'),
        ),
        migrations.AddField(
            model_name='estimatedstationprimarypollutantitem',
            name='station_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primary_pollutants', related_query_name='primary_pollutant', to='airquality.EstimatedStationRecord'),
        ),
        migrations.AddField(
            model_name='estimatedcityprimarypollutantitem',
            name='city_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primary_pollutants', related_query_name='primary_pollutant', to='airquality.EstimatedCityRecord'),
        ),
        migrations.AddField(
            model_name='cityprimarypollutantitem',
            name='city_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='primary_pollutants', related_query_name='primary_pollutant', to='airquality.CityRecord'),
        ),
        migrations.AlterUniqueTogether(
            name='stationrecord',
            unique_together=set([('city_record', 'station')]),
        ),
        migrations.AlterUniqueTogether(
            name='stationprimarypollutantitem',
            unique_together=set([('station_record', 'pollutant')]),
        ),
        migrations.AlterUniqueTogether(
            name='station',
            unique_together=set([('city', 'name_cn')]),
        ),
        migrations.AlterUniqueTogether(
            name='estimatedstationprimarypollutantitem',
            unique_together=set([('station_record', 'pollutant')]),
        ),
        migrations.AlterUniqueTogether(
            name='estimatedcityprimarypollutantitem',
            unique_together=set([('city_record', 'pollutant')]),
        ),
        migrations.AlterUniqueTogether(
            name='cityrecord',
            unique_together=set([('city', 'update_dtm')]),
        ),
        migrations.AlterUniqueTogether(
            name='cityprimarypollutantitem',
            unique_together=set([('city_record', 'pollutant')]),
        ),
    ]
