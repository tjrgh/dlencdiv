from django.db import models

# Create your models here.
from django.db import models
from ubold.common.models import TimeStampMixin
from ubold.stocks.models import BasicInfo
from django.contrib.auth.models import User


class PortfolioInfo(TimeStampMixin):
    """PortfolioInfo
    포트폴리오 기본 정보"""
    name = models.TextField(help_text='이름')
    earn_rate = models.FloatField(default=0, help_text='수익율')
    is_recommend = models.BooleanField(default=False, help_text='추천 여부')
    is_favorite = models.BooleanField(default=False, help_text='인기 여부')
    user_made = models.BooleanField(default=False, help_text='유저 생성 여부')
    create_by = models.ForeignKey(
        User
        , related_name='portfolio'
        , on_delete=models.PROTECT
        , help_text='생성한 유저'
    )
    description = models.TextField(blank=True, default=' ', help_text='설명')

    class Meta:
        db_table = 'portfolio_info'
        indexes = [
            models.Index(fields=['is_recommend']),
            models.Index(fields=['is_favorite']),
        ]


class PortfolioStocks(TimeStampMixin):
    """PortfolioStocks
    포트폴리오를 구성하는 주식"""

    portfolio = models.ForeignKey(
        'PortfolioInfo'
        , related_name='stocks'
        , on_delete=models.PROTECT
        , help_text='해당 포트폴리오'
    )
    stock_code = models.ForeignKey(
        BasicInfo
        , related_name='portfolio'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    percentage = models.FloatField(default=0, help_text='비중')

    class Meta:
        db_table = 'portfolio_stocks'
        indexes = [
            models.Index(fields=['portfolio', 'stock_code', '-created_at'])
        ]
