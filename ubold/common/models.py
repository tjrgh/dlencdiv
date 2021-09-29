from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from pytz import timezone

class TimeStampMixin(models.Model):
    """
    생성일, 수정일 추상화 모델
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text='생성일시')
    updated_at = models.DateTimeField(auto_now=True, help_text='수정일시')

    class Meta:
        abstract = True


class Currency(TimeStampMixin):
    """
    통화 코드
    """
    name = models.CharField(max_length=30, help_text='통화 이름')
    code = models.CharField(max_length=3, unique=True, help_text='통화 코드')
    number = models.IntegerField(help_text='통화 번호')
    is_use = models.BooleanField(default=True, help_text='사용여부')

    class Meta:
        db_table = 'common_currency'
        # 통화 이름-사용여부 인덱스, 사용여부 인덱스
        indexes = [
            models.Index(fields=['name', 'is_use'], name='common_currency_name_idx')
            , models.Index(fields=['is_use'], name='common_currency_is_use_idx')
        ]

    def __str__(self):
        return self.name


class Market(TimeStampMixin):
    """
    주식 시장
    """
    name = models.CharField(max_length=30, help_text='주식 시장명')
    code = models.CharField(max_length=10, unique=True, help_text='주식 시장 코드')
    is_use = models.BooleanField(default=True, help_text='사용여부')

    class Meta:
        db_table = 'common_market'
        # 주식 시장명-사용여부 인덱스, 사용여부 인덱스
        indexes = [
            models.Index(fields=['name', 'is_use'], name='common_market_name_idx')
            , models.Index(fields=['is_use'], name='common_market_is_use_idx')
        ]

    def __str__(self):
        return self.code
