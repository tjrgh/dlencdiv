# Generated by Django 3.1.8 on 2021-09-29 05:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stocks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortfolioInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='생성일시')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='수정일시')),
                ('name', models.TextField(help_text='이름')),
                ('earn_rate', models.FloatField(default=0, help_text='수익율')),
                ('is_recommend', models.BooleanField(default=False, help_text='추천 여부')),
                ('is_favorite', models.BooleanField(default=False, help_text='인기 여부')),
                ('user_made', models.BooleanField(default=False, help_text='유저 생성 여부')),
                ('description', models.TextField(blank=True, default=' ', help_text='설명')),
                ('create_by', models.ForeignKey(help_text='생성한 유저', on_delete=django.db.models.deletion.PROTECT, related_name='portfolio', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'portfolio_info',
            },
        ),
        migrations.CreateModel(
            name='PortfolioStocks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='생성일시')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='수정일시')),
                ('percentage', models.FloatField(default=0, help_text='비중')),
                ('portfolio', models.ForeignKey(help_text='해당 포트폴리오', on_delete=django.db.models.deletion.PROTECT, related_name='stocks', to='portfolio.portfolioinfo')),
                ('stock_code', models.ForeignKey(help_text='종목코드', on_delete=django.db.models.deletion.PROTECT, related_name='portfolio', to='stocks.basicinfo', to_field='code')),
            ],
            options={
                'db_table': 'portfolio_stocks',
            },
        ),
        migrations.AddIndex(
            model_name='portfoliostocks',
            index=models.Index(fields=['portfolio', 'stock_code', '-created_at'], name='portfolio_s_portfol_28c6e9_idx'),
        ),
        migrations.AddIndex(
            model_name='portfolioinfo',
            index=models.Index(fields=['is_recommend'], name='portfolio_i_is_reco_7781c7_idx'),
        ),
        migrations.AddIndex(
            model_name='portfolioinfo',
            index=models.Index(fields=['is_favorite'], name='portfolio_i_is_favo_6b80e4_idx'),
        ),
    ]