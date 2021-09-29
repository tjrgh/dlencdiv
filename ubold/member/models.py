from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from ubold.common.models import TimeStampMixin
from ubold.stocks.models import BasicInfo


class TradeLog(TimeStampMixin):
    """
    회원의 거래기록
    """

    class TradeType(models.IntegerChoices):
        """
        거래구분 enum
        매수: 1
        매도: 2
        """
        BUY = 1
        SELL = 2

    user = models.OneToOneField(User, on_delete=models.CASCADE, help_text='회원')
    stock = models.ForeignKey(
        'stocks.BasicInfo'
        , on_delete=models.PROTECT
        , help_text='종목'
    )
    number = models.IntegerField(help_text='거래 수')
    price = models.DecimalField(max_digits=19, decimal_places=2, help_text='거래 가격')
    trade_type = models.IntegerField(choices=TradeType.choices, help_text='거래구분, 1: 매수 2: 매도')

    class Meta:
        db_table = 'user_trade_log'
        indexes = [
            models.Index(fields=['-created_at'], name='user_trade_log_created_at_idx')  # 생성일 내림차순 인덱스
        ]


class MyStocks(TimeStampMixin):
    """
    회원 보유 종목
    """

    class MyStockType(models.IntegerChoices):
        """
        보유 구분
        보유: 1
        관심: 2
        """
        HAVE = 1
        INTEREST = 2

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL
        , on_delete=models.PROTECT
        , related_name='myHold'
        , help_text='회원'
    )
    stock = models.ForeignKey(
        'stocks.BasicInfo'
        , on_delete=models.PROTECT
        , related_name='userHold'
        , help_text='종목'
    )
    type = models.IntegerField(choices=MyStockType.choices, help_text='보유 구분 1: 보유 2: 관심')

    class Meta:
        db_table = 'user_my_stocks'
        indexes = [
            models.Index(fields=['user', 'type'], name='user_my_stocks_user_type_idx')
        ]


class MyPortfolio(TimeStampMixin):
    """MyPortfolio
    회원 보유 포트폴리오
    """

    class MyPortfolioType(models.IntegerChoices):
        """
        보유 구분
        보유: 1
        관심: 2
        """
        HAVE = 1
        INTEREST = 2

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL
        , on_delete=models.PROTECT
        , related_name='my_portfolio'
        , help_text='회원'
    )
    portfolio = models.ForeignKey(
        'portfolio.PortfolioInfo'
        , on_delete=models.PROTECT
        , related_name='user_portfolio'
        , help_text='포트폴리오'
    )
    type = models.IntegerField(choices=MyPortfolioType.choices, help_text='보유 구분 1: 보유 2: 관심')
    amount = models.BigIntegerField(default=0, help_text='투자금액')
    is_delete = models.BooleanField(default=False, help_text='삭제여부')
    create_date = models.DateTimeField(default=None, null=True, help_text='생성날짜')

    class Meta:
        db_table = 'user_my_portfolio'
        indexes = [
            models.Index(fields=['user', 'type'], name='user_my_port_user_type_idx')
        ]


class MyPortfolioStocks(TimeStampMixin):
    """MyPortfolioStocks
    내 포트폴리오를 구성하는 주식"""

    portfolio = models.ForeignKey(
        'MyPortfolio'
        , related_name='stocks'
        , on_delete=models.PROTECT
        , help_text='해당 내 포트폴리오'
    )
    stock_code = models.ForeignKey(
        BasicInfo
        , related_name='my_portfolio'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    percentage = models.FloatField(default=0, help_text='비중')
    hold_number = models.IntegerField(default=0, help_text='보유 주 수')
    buy_price = models.DecimalField(default=0, decimal_places=2, max_digits=12, help_text='구매 시 단가')
    total_price = models.DecimalField(default=0, decimal_places=2, max_digits=12, help_text='구매 시 총 액')

    class Meta:
        db_table = 'user_my_portfolio_stocks'
        indexes = [
            models.Index(fields=['portfolio', 'stock_code', '-created_at'])
        ]
