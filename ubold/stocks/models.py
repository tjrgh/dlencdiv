from django.db import models

# Create your models here.
from django.db import models
from ubold.common.models import TimeStampMixin
from datetime import date
from django.utils import timezone


class BasicInfo(TimeStampMixin):
    """
    주식 종목 기본정보
    """
    DEFAULT_CURRENCY_ID = 1
    DEFAULT_MARKET_ID = 1

    code = models.CharField(max_length=7, unique=True, help_text='종목코드')
    name = models.CharField(max_length=20, help_text='종목명')
    market = models.ForeignKey(
        'common.Market'
        , on_delete=models.PROTECT
        , help_text='시장'
        , default=DEFAULT_MARKET_ID
    )
    currency = models.ForeignKey(
        'common.Currency'
        , on_delete=models.PROTECT
        , help_text='사용 통화'
        , default=DEFAULT_CURRENCY_ID
    )
    corp_code = models.CharField(max_length=9, blank=True, default=' ', help_text='DART 고유번호')
    is_recommend = models.BooleanField(default=False, help_text='추천 종목')
    is_favorite = models.BooleanField(default=False, help_text='인기 종목')

    class Meta:
        db_table = 'stocks_basic_info'
        indexes = [
            models.Index(fields=['name'], name='stocks_basic_info_name_idx')  # 주식 종목명 인덱스
        ]
        ordering = ('code',)


class DetailInfo(TimeStampMixin):
    """
    주식 종목 상세정보
    """
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='details'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    time = models.BigIntegerField(help_text='시간 (hhmm)')
    updown_signal = models.IntegerField(
        choices=models.IntegerChoices('SignalType', '상한 상승 보합 하한 하락').choices
        , help_text='대비부호'
    )
    updown_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='전일대비')
    current_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='현재가')
    open_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='시가')
    high_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='고가')
    low_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='저가')
    ask_quote = models.DecimalField(max_digits=19, decimal_places=2, help_text='매도호가')
    bid_quote = models.DecimalField(max_digits=19, decimal_places=2, help_text='매수호가')
    transaction_volume = models.BigIntegerField(help_text='거래량')
    transaction_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='거래대금')
    market_state = models.IntegerField(
        choices=models.IntegerChoices('MarketStateCode', '장전 동시호가 장중 빈값').choices
        , default=4
        , help_text='장구분. 1: 장전, 2: 동시호가, 3: 장중, 4: 빈값'
    )
    total_ask_quote_redundancy = models.BigIntegerField(help_text='총매도호가잔량')
    total_bid_quote_redundancy = models.BigIntegerField(help_text='총매수호가잔량')
    first_ask_quote_redundancy = models.BigIntegerField(help_text='최우선매도호가잔량')
    first_bid_quote_redundancy = models.BigIntegerField(help_text='최우선매수호가잔량')
    total_listing_volume = models.BigIntegerField(help_text='총상장주식수')
    foreigner_holding_ration = models.FloatField(help_text='회국인보유비율')
    previous_volume = models.BigIntegerField(help_text='전일거래량')
    previous_close_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='전일종가')
    volume_power = models.FloatField(help_text='체결강도')
    volume_type = models.IntegerField(
        choices=models.IntegerChoices('VolumeTypeCode', '매수체결 매도체결 빈값').choices
        , default=3
        , help_text='체결구분. 1: 매수체결, 2: 매도체결, 3: 빈값'
    )
    open_interest = models.BigIntegerField(help_text='미결제약정')
    expected_closing_price = models.BigIntegerField(help_text='예상체결가')
    expected_closing_updown = models.BigIntegerField(help_text='예상체결가대비')
    expected_closing_updown_signal = models.IntegerField(
        choices=models.IntegerChoices('SignalType', '상한 상승 보합 하한 하락 빈값').choices
        , help_text='예상체결가 대비부호'
    )
    expected_volume = models.BigIntegerField(help_text='예상체결수량')
    nineteen_closing_sum = models.DecimalField(max_digits=19, decimal_places=2, help_text='19일 종가합')
    upper_limit = models.DecimalField(max_digits=19, decimal_places=2, help_text='상한가')
    lower_limit = models.DecimalField(max_digits=19, decimal_places=2, help_text='하한가')
    sales_quantity_unit = models.PositiveSmallIntegerField(help_text='매매수량단위')
    foreigner_net_sale_volume = models.BigIntegerField(help_text='외국인순매매. 단위: 주')
    fiftytwoweek_high_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='52주 최고가')
    fiftytwoweek_low_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='52주 최저가')
    year_high_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='연중 최고가')
    year_low_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='연중 최저가')
    price_earning_ratio = models.FloatField(help_text='PER')
    earning_per_share = models.BigIntegerField(help_text='EPS')
    capital = models.BigIntegerField(help_text='자본금. 단위: 백만')
    par_value = models.PositiveSmallIntegerField(help_text='액면가')
    allocation_ratio = models.FloatField(help_text='배당률')
    allocation_earning_ratio = models.FloatField(help_text='배당수익률')
    debt_ratio = models.FloatField(help_text='부채비율')
    reservation_ratio = models.FloatField(help_text='유보율')
    equity_capital_ratio = models.FloatField(help_text='자기자본이익률')
    sales_growth_ratio = models.FloatField(help_text='매출이익증가율')
    ordinary_profit_growth_ratio = models.FloatField(help_text='경상이익증가율')
    net_profit_growth_ratio = models.FloatField(help_text='순이익증가율')
    sentiment_indicators = models.FloatField(help_text='투자심리')
    volume_ratio = models.FloatField(help_text='VR')
    fiveday_turnover_ratio = models.FloatField(help_text='5일 회전율')
    fourday_closeprice_sum = models.DecimalField(max_digits=19, decimal_places=2, help_text='4일 종가합')
    nineday_closeprice_sum = models.DecimalField(max_digits=19, decimal_places=2, help_text='9일 종가합')
    revenue = models.BigIntegerField(help_text='매출액. 단위: 백만')
    ordinary_profit = models.BigIntegerField(help_text='경상이익. 단위: 원')
    net_profit = models.BigIntegerField(help_text='당기 순이익. 단위: 원')
    bookvalue_per_share = models.BigIntegerField(help_text='BPS 주당 순 자산')
    operating_income_growth_ratio = models.FloatField(help_text='영업이익증가율')
    operating_income = models.DecimalField(max_digits=19, decimal_places=2, help_text='영업이익')
    operating_income_to_sales_ratio = models.FloatField(help_text='매출액영업이익률')
    ordinary_profit_to_sales_ratio = models.FloatField(help_text='매출액경상이익률')
    interest_coverage_ratio = models.FloatField(help_text='이자보상비율')
    closing_account_date = models.PositiveIntegerField(help_text='결산년월 yyyyMM')
    quarter_bookvalue_per_share = models.BigIntegerField(help_text='분기BPS. 분기주당순자산')
    quarter_revenue_growth_ratio = models.FloatField(help_text='분기매출액증가율')
    quarter_operating_income_growth_ratio = models.FloatField(help_text='분기영업이익증가율')
    quarter_ordinary_profit_growth_ratio = models.FloatField(help_text='분기경상이익증가율')
    quarter_net_profit_growth_ratio = models.FloatField(help_text='분기순이익증가율')
    quarter_sales = models.DecimalField(max_digits=19, decimal_places=2, help_text='분기매출액. 단위: 백만')
    quarter_operating_income = models.DecimalField(max_digits=19, decimal_places=2, help_text='분기영업이익. 단위: 원')
    quarter_ordinary_profit = models.DecimalField(max_digits=19, decimal_places=2, help_text='분기경상이익. 단위: 원')
    quarter_net_profit = models.DecimalField(max_digits=19, decimal_places=2, help_text='분기당기순이익. 단위: 원')
    quarter_operating_income_to_sales_ratio = models.FloatField(help_text='분기매출액영업이익률')
    quarter_ordinary_profit_to_sales_ratio = models.FloatField(help_text='분기매출액경상이익률')
    quarter_return_on_equity = models.FloatField(help_text='분기 ROE. 자기자본순이익률')
    quarter_interest_coverage_ratio = models.FloatField(help_text='분기이자보상비율')
    quarter_reserve_ratio = models.FloatField(help_text='분기유보율')
    quarter_debr_ration = models.FloatField(help_text='분기부채비율')
    last_quarter_yyyymm = models.PositiveIntegerField(help_text='최근분기년월 yyyyMM')
    basis = models.FloatField(help_text='BASIS')
    local_date_yyyymmdd = models.PositiveIntegerField(help_text='현지날짜 yyyyMMdd')
    nation = models.TextField(help_text='해외지수국가명')
    elw_theoretical_value = models.DecimalField(max_digits=19, decimal_places=2, help_text='ELW 이론가')
    program_net_bid = models.BigIntegerField(help_text='프로그램 순 매수')
    today_foregier_net_bid_porvisional_yesno = models.IntegerField(
        choices=models.IntegerChoices('YesNoType', '해당없음 확정 잠정').choices
        , help_text='당일외국인순매수잠정구분'
    )
    today_foregier_net_bid = models.BigIntegerField(help_text='당일 외국인 순매수')
    today_institution_net_bid_porvisional_yesno = models.IntegerField(
        choices=models.IntegerChoices('YesNoType', '해당없음 확정 잠정').choices
        , help_text='당일기관순매수잠정구분'
    )
    today_institution_net_bid = models.BigIntegerField(help_text='당일 기관 순매수')
    previous_foregier_net_bid = models.BigIntegerField(help_text='전일 외국인 순매수')
    previous_institution_net_bid = models.BigIntegerField(help_text='전일 기관 순매수')
    sales_per_share = models.DecimalField(max_digits=19, decimal_places=2, help_text='SPS')
    cash_flow_per_share = models.DecimalField(max_digits=19, decimal_places=2, help_text='CFPS')
    earning_before_interest_tax_depreciation_amortization = models.DecimalField(
        max_digits=19, decimal_places=2, help_text='EVITDA'
    )
    credit_balance_ratio = models.FloatField(help_text='신용잔고율')
    short_selling_quantity = models.BigIntegerField(help_text='공매도수량')
    short_selling_date = models.BigIntegerField(help_text='공매도일자')
    index_futures_previous_unpaid_agreement = models.BigIntegerField(
        help_text='지수/주식선물 전일미결제약정'
    )
    beta = models.FloatField(help_text='베타계수')
    fiftynine_close_sum = models.DecimalField(max_digits=19, decimal_places=2, help_text='59일 종가 합')
    oneonenine_close_sum = models.DecimalField(max_digits=19, decimal_places=2, help_text='119일 종가 합')
    today_retail_net_bid_porvisional_yesno = models.IntegerField(
        choices=models.IntegerChoices('YesNoType', '해당없음 확정 잠정').choices
        , help_text='당일 개인 순매수 잠정구분'
    )
    today_retail_net_bid = models.BigIntegerField(help_text='당일 개인 순매수')
    previous_retail_net_bid = models.BigIntegerField(help_text='전일 개인 순매수')
    five_previous_close_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='5일 전 종가')
    ten_previous_close_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='10일 전 종가')
    twenty_previous_close_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='20일 전 종가')
    sixty_previous_close_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='60일 전 종가')
    onehundredtwenty_previous_close_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='120일 전 종가')
    estimated_static_vi_activation_base_price = models.DecimalField(
        max_digits=19, decimal_places=2, help_text='정적 VI 발동 예상 기준가'
    )
    estimated_static_vi_activation_rising_price = models.DecimalField(
        max_digits=19, decimal_places=2, help_text='정적 VI 발동 예상 상승가'
    )
    estimated_static_vi_activation_falling_price = models.DecimalField(
        max_digits=19, decimal_places=2, help_text='정적 VI 발동 예상 하락가'
    )
    data_date = models.DateField(auto_now_add=True, help_text='입력 날짜')

    class Meta:
        db_table = 'stocks_detail_info'
        unique_together = ['code', 'data_date']

    def __str__(self):
        return str(self.current_price)


class Parameter(TimeStampMixin):
    """
    주식 종목별 점수
    """
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='parameters'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    attractive = models.FloatField(help_text='배당 매력')
    growth = models.FloatField(help_text='성장성')
    stability = models.FloatField(help_text='재무 안정성')
    cash_generate = models.FloatField(help_text='현금 창출력')
    monopoly = models.FloatField(help_text='독점력')
    recommendation_value = models.IntegerField(help_text='추천 점수')
    data_date = models.DateField(auto_now_add=True, help_text='데이터 날짜')

    class Meta:
        db_table = 'stocks_parameter'
        unique_together = ['code', 'data_date']
        indexes = [
            models.Index(fields=['-data_date'], name='stocks_parameters_date_idx'),  # 날짜 인덱스
        ]


class HistoricData(TimeStampMixin):
    """HistoricData
    과거데이타
    """
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='historic'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    close = models.IntegerField
    close_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='종가')
    open_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='시가')
    high_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='고가')
    low_price = models.DecimalField(max_digits=19, decimal_places=2, help_text='저가')
    transaction_volume = models.BigIntegerField(help_text='거래량')
    date = models.DateField(help_text='날짜')

    class Meta:
        db_table = 'stocks_historic_data'
        unique_together = ['code', 'date']


class StocksSignal(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='signals'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    stock_name = models.CharField(max_length=300, help_text='종목명')
    signal = models.TextField(help_text='특이사항')
    date = models.DateField(help_text='날짜')
    time = models.CharField(max_length=10, help_text='시간')

    class Meta:
        db_table = 'stocks_signal'
        indexes = [
            models.Index(fields=['-date', '-time'], name='stocks_signal_date_time_idx'),  # 날짜 인덱스
        ]


class StockReports(TimeStampMixin):
    stock_name = models.CharField(max_length=20, help_text='종목명')
    stock_code = models.CharField(max_length=6, help_text='종목코드')
    title = models.CharField(max_length=100, help_text='제목')
    link = models.TextField(help_text='보고서 링크 url')
    fin_corp = models.CharField(max_length=20, help_text='증권사')
    date = models.DateField(help_text='작성일')

    class Meta:
        db_table = 'stocks_reports'
        indexes = [
            models.Index(fields=['stock_name'], name='stocks_reports_name'),
            models.Index(fields=['stock_code'], name='stocks_reports_code'),
        ]


class FinancialStatement(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='fin_statement'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    business_year = models.CharField(max_length=5, help_text='사업년도')
    business_month = models.CharField(max_length=5, help_text='사업월')
    this_term_name = models.CharField(max_length=100, help_text='당기 명')
    subject_name = models.CharField(max_length=10, help_text='재무제표명')
    account_id = models.CharField(max_length=500, help_text='계정 ID')
    account_name = models.CharField(max_length=100, help_text='계정명')
    account_level = models.IntegerField(help_text='LV')
    this_term_amount = models.DecimalField(
        max_digits=21, decimal_places=2, help_text='당기 금액'
    )
    ordering = models.IntegerField(help_text='계정과목 정렬순서')

    class Meta:
        db_table = 'stock_financial_statement'
        unique_together = ["code", "this_term_name", "subject_name", "account_id"]
        indexes = [
            models.Index(fields=['corp_code'], name='stock_fin_corp_code_idx'),
            models.Index(fields=['subject_name'], name='stock_fin_sub_name_idx'),
            models.Index(fields=['corp_code', 'subject_name', 'this_term_name'], name='stock_fin_corp_sub_term_idx'),
        ]


class SectorStatement(TimeStampMixin):
    sector_name = models.CharField(max_length=50, help_text='섹터명')
    date = models.DateField(help_text='일자')
    account_name = models.CharField(max_length=100, help_text='계정명')
    amount = models.DecimalField(
        max_digits=21, decimal_places=2, help_text='데이터 값'
    )

    class Meta:
        db_table = 'stock_sector_statement'
        indexes = [
            models.Index(fields=['sector_name'], name='sector_name_idx'),
            models.Index(fields=['account_name'], name='sector_acc_idx'),
            models.Index(fields=['sector_name', 'account_name'], name='sector_name_acc_idx'),
        ]


class MentionCounts(TimeStampMixin):
    class TermType(models.TextChoices):
        D = "d", "일"
        W = "w", "주"
        M = "m", "월"
        Q = "q", "분기"
        H = "h", "반기"

    code = models.ForeignKey(
        'BasicInfo'
        , related_name='mention_counts'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_type = models.CharField(
        max_length=10,
        choices=TermType.choices,
        default=TermType.D,
        help_text='집계 기간 단위 : d(일), w(주), m(월), q(분기), h(반기)'
    )
    term_start = models.CharField(max_length=10, help_text='기간 시작일')
    term_end = models.CharField(max_length=10, help_text='기간 종료일')
    community_count = models.IntegerField(help_text='커뮤니티 언급량')
    insta_count = models.IntegerField(help_text='인스타 언급량')
    blog_count = models.IntegerField(help_text='블로그 언급량')
    news_count = models.IntegerField(help_text='뉴스 언급량')
    twitter_count = models.IntegerField(help_text='트위터 언급량')
    count_sum = models.IntegerField(help_text='언급량 합')

    class Meta:
        db_table = 'stock_mention_counts'
        indexes = [
            models.Index(fields=['corp_code'], name='mention_counts_corp_code_idx'),
            models.Index(fields=['term_type'], name='mention_counts_term_type_idx'),
            # models.Index(fields=['corp_code', 'subject_name', 'this_term_name'], name='stock_fin_corp_sub_term_idx'),
        ]


class ConnectionWords(TimeStampMixin):
    class TermType(models.TextChoices):
        D = "d", "일"
        W = "w", "주"
        M = "m", "월"
        Q = "q", "분기"
        H = "h", "반기"

    code = models.ForeignKey(
        'BasicInfo'
        , related_name='connection_words'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_type = models.CharField(
        max_length=10,
        choices=TermType.choices,
        default=TermType.D,
        help_text='집계 기간 단위 : d(일), w(주), m(월), q(분기), h(반기)'
    )
    term_start = models.CharField(max_length=10, help_text='기간 시작일')
    term_end = models.CharField(max_length=10, help_text='기간 종료일')
    word = models.CharField(max_length=50, help_text='단어')
    word_count = models.IntegerField(help_text='단어 수')
    rank = models.IntegerField(help_text='단어 수 순위')
    category1 = models.CharField(max_length=100, help_text='카테고리(대분류)')
    category2 = models.CharField(max_length=100, help_text='카테고리(소분류)')

    class Meta:
        db_table = 'stock_connection_words'
        indexes = [
            models.Index(fields=['corp_code'], name='connection_words_corp_code_idx'),
            models.Index(fields=['term_type'], name='connection_words_term_type_idx'),
            # models.Index(fields=['corp_code', 'subject_name', 'this_term_name'], name='stock_fin_corp_sub_term_idx'),
        ]


class PosNegWords(TimeStampMixin):
    class TermType(models.TextChoices):
        D = "d", "일"
        W = "w", "주"
        M = "m", "월"
        Q = "q", "분기"
        H = "h", "반기"

    class PosNeg(models.TextChoices):
        POS = "pos", "긍정"
        NEG = "neg", "부정"
        NEU = "neu", "중립"

    code = models.ForeignKey(
        'BasicInfo'
        , related_name='pos_neg_words'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_type = models.CharField(
        max_length=10,
        choices=TermType.choices,
        default=TermType.D,
        help_text='집계 기간 단위 : d(일), w(주), m(월), q(분기), h(반기)'
    )
    term_start = models.CharField(max_length=10, help_text='기간 시작일')
    term_end = models.CharField(max_length=10, help_text='기간 종료일')
    word = models.CharField(max_length=50, help_text='단어')
    word_count = models.IntegerField(help_text='단어 수')
    rank = models.IntegerField(help_text='단어 수 순위')
    pos_neg = models.CharField(
        max_length=10,
        choices=PosNeg.choices,
        default=PosNeg.NEU,
        help_text='긍/부정 : pos(긍정), neg(부정), neu(중립)'
    )
    property = models.CharField(max_length=100, help_text='속성')

    class Meta:
        db_table = 'stock_pos_neg_words'
        indexes = [
            models.Index(fields=['corp_code'], name='pos_neg_words_corp_code_idx'),
            models.Index(fields=['term_type'], name='pos_neg_words_term_type_idx'),
            # models.Index(fields=['corp_code', 'subject_name', 'this_term_name'], name='stock_fin_corp_sub_term_idx'),
        ]


class SocialKeywords(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='social_keywords'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
        , null=True
    )
    corp_code = models.CharField(null=True, max_length=9, help_text='DART 고유번호')
    keyword = models.CharField(max_length=50, help_text='검색 키워드')
    equal_keyword_list = models.CharField(blank=True, default='', max_length=500, help_text='동의어 목록')
    or_include_keyword_list = models.CharField(blank=True, default='', max_length=500, help_text="'또는' 포함어 목록")
    and_include_keyword_list = models.CharField(blank=True, default='', max_length=500, help_text="'그리고' 포함어 목록")
    exclude_keyword_list = models.CharField(blank=True, default='', max_length=500, help_text='제외어 목록')
    is_followed = models.BooleanField(default=True, help_text="지속적 수집 여부")

    class Meta:
        db_table = 'social_keywords'
        unique_together = ["code", "keyword", "equal_keyword_list", "or_include_keyword_list",
                           "and_include_keyword_list", "exclude_keyword_list"]


class SocialSearchList(TimeStampMixin):
    keyword = models.ForeignKey(
        'SocialKeywords'
        , related_name='social_search_list'
        , on_delete=models.PROTECT
        , to_field='id'
        , help_text='키워드 id'
        , null=False
    )
    term_start = models.CharField(max_length=10, help_text="기간 시작")
    term_end = models.CharField(max_length=10, help_text="기간 종료")
    completed = models.BooleanField(help_text="검색 완료")

    class Meta:
        db_table = 'social_search_list'


class StockNews(TimeStampMixin):
    stock_name = models.CharField(max_length=20, help_text='종목명')
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='stock_news'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    title = models.CharField(max_length=100, help_text='제목')
    link = models.TextField(help_text='뉴스 링크 url')
    source = models.CharField(max_length=20, help_text='소스 사이트')
    date = models.DateField(help_text='작성일')

    class Meta:
        db_table = 'stocks_news'
        indexes = [
            models.Index(fields=['code'], name='stocks_news_code')
        ]


class news_reactions(TimeStampMixin):
    """
    뉴스의 반응을 스크래핑한 테이블.
    """
    stock_name = models.CharField(max_length=20, help_text='종목명')
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='news_reactions'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    title = models.CharField(max_length=100, help_text='제목')
    link = models.TextField(help_text='뉴스 링크 url')
    press = models.CharField(null=True, max_length=20, help_text='언론사')
    source = models.CharField(max_length=20, help_text='소스 사이트')
    date = models.DateField(help_text='작성일')
    emotion_count = models.IntegerField(null=True, help_text='감정 반응 개수')
    comment_count = models.IntegerField(null=True, help_text='댓글 개수')
    emotion_like_cnt = models.IntegerField(null=True, help_text='감정 반응 좋아요 개수')
    emotion_warm_cnt = models.IntegerField(null=True, help_text='감정 반응 훈훈해요 개수')
    emotion_sad_cnt = models.IntegerField(null=True, help_text='감정 반응 슬퍼요 개수')
    emotion_angry_cnt = models.IntegerField(null=True, help_text='감정 반응 화나요 개수')
    emotion_want_cnt = models.IntegerField(null=True, help_text='감정 반응 후속기사 원해요 개수')
    emotion_recommend_cnt = models.IntegerField(null=True, help_text='감정 반응 추천해요')

    class Meta:
        db_table = 'news_reactions'
        indexes = [
            models.Index(fields=['code'], name='news_reactions_code')
        ]


class ReportSummary(TimeStampMixin):
    # class SelBuy(models.TextChoices):
    #     SEL = "sel", "매각"
    #     BUY = "buy", "매수"
    #     NEU = "neu", "중립"
    #     NR = "not rated", "not rated"

    stock_name = models.CharField(max_length=20, help_text='종목명')
    # code = models.ForeignKey(
    #     'BasicInfo'
    #     , related_name='report_summary'
    #     , on_delete=models.PROTECT
    #     , to_field='code'
    #     , help_text='종목코드'
    # )
    code = models.CharField(max_length=7, help_text="종목코드")
    title = models.CharField(max_length=100, help_text='제목')
    summary = models.CharField(max_length=500, help_text='요약')
    decision = models.CharField(max_length=15, help_text='매각/매수')
    target_price = models.IntegerField(null=True, help_text="목표 주가")
    current_price = models.IntegerField(null=True, help_text="전일 종가")
    link = models.TextField(null=True, help_text='보고서 링크 url')
    fin_corp = models.CharField(max_length=20, help_text='증권사')
    writer = models.CharField(max_length=20, help_text="작성자")
    date = models.DateField(help_text='작성일')

    class Meta:
        db_table = 'report_summary'
        indexes = [
            models.Index(fields=['code'], name='report_summary_code'),
        ]


class Consensus(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='consensus'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    estimate_date = models.DateField(help_text='추정일자')
    target_year = models.CharField(max_length=4, help_text='예측 년도')
    fin_corp = models.CharField(max_length=20, help_text='증권사')
    com_sep = models.CharField(max_length=3, help_text='연결/개별')
    account_name = models.CharField(max_length=100, help_text='계정명')
    lastest_estimate = models.DecimalField(null=True, max_digits=21, decimal_places=2, help_text='최신 추정치')
    before_estimate = models.DecimalField(null=True, max_digits=21, decimal_places=2, help_text='직전 추정치')

    class Meta:
        db_table = 'consensus'
        unique_together = ["code", "target_year", "fin_corp", "estimate_date", "account_name"]
        indexes = [
            models.Index(fields=['corp_code'], name='consensus_corp_code_idx'),
            models.Index(fields=['code'], name='consensus_code_idx'),
            models.Index(fields=['code', 'fin_corp'], name='consensus_code_fin_corp_idx'),
        ]


class Shareholder(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='shareholder'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_name = models.CharField(max_length=10, help_text='기간')
    shareholder_name = models.CharField(max_length=50, help_text='주주')
    share_per = models.DecimalField(null=True, max_digits=21, decimal_places=2, help_text='지분')

    class Meta:
        db_table = 'shareholder'
        unique_together = ["code", "term_name", "shareholder_name"]
        indexes = [
            models.Index(fields=['corp_code'], name='shareholder_corp_code_idx'),
            models.Index(fields=['code'], name='shareholder_code_idx'),
        ]


class Dividend(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='dividend'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_name = models.CharField(max_length=10, help_text='기간명')
    account_name = models.CharField(max_length=50, help_text='계정명')
    value = models.DecimalField(null=True, max_digits=21, decimal_places=2, help_text='값')

    class Meta:
        db_table = 'dividend'
        unique_together = ["code", "term_name", "account_name"]
        indexes = [
            models.Index(fields=['corp_code'], name='dividend_corp_code_idx'),
            models.Index(fields=['code'], name='dividend_code_idx'),
        ]


class AfAndSub(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='af_and_sub'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_name = models.CharField(max_length=10, help_text='기간명')
    relative_stock_code = models.CharField(max_length=15, help_text='대상 회사 종목 코드')
    account_name = models.CharField(max_length=50, help_text='계정명')
    value = models.DecimalField(null=True, max_digits=21, decimal_places=2, help_text='값')

    class Meta:
        db_table = 'af_and_sub'
        unique_together = ["code", "term_name", "relative_stock_code", "account_name"]
        indexes = [
            models.Index(fields=['corp_code'], name='af_and_sub_corp_code_idx'),
            models.Index(fields=['code'], name='af_and_sub_code_idx'),
        ]


class WorkerCountAndPay(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='worker_count_pay'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_name = models.CharField(max_length=10, help_text='기간명')
    worker_category = models.CharField(max_length=20, help_text='종업원 카테고리')
    worker_sex = models.CharField(max_length=1, help_text="종업원 성별")
    item_name = models.CharField(max_length=50, help_text='항목명')
    value = models.DecimalField(null=True, max_digits=21, decimal_places=2, help_text='값')

    class Meta:
        db_table = 'worker_count_pay'
        unique_together = ["code", "term_name", "worker_category", "worker_sex", "item_name"]
        indexes = [
            models.Index(fields=['corp_code'], name='worker_count_pay_corp_code_idx'),
            models.Index(fields=['code'], name='worker_count_pay_code_idx'),
        ]


class ExecutiveWage(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='executive_wage'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_name = models.CharField(max_length=10, help_text='기간명')
    worker_name = models.CharField(max_length=20, help_text='임원 이름')
    worker_position = models.CharField(null=True, max_length=30, help_text="직책")
    wage = models.DecimalField(max_digits=21, decimal_places=2, help_text='보수액')

    class Meta:
        db_table = 'executive_wage'
        unique_together = ["code", "term_name", "worker_name", "worker_position"]
        indexes = [
            models.Index(fields=['corp_code'], name='executive_wage_corp_code_idx'),
            models.Index(fields=['code'], name='executive_wage_code_idx'),
        ]


class Executives(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='executives'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_name = models.CharField(max_length=10, help_text='기간명')
    worker_name = models.CharField(max_length=20, help_text='임원 이름')
    worker_position = models.CharField(null=True, max_length=30, help_text="직책")
    worker_birth_date = models.CharField(null=True, max_length=10, help_text="생년월일")

    class Meta:
        db_table = 'executives'
        unique_together = ["code", "term_name", "worker_name", "worker_birth_date", "worker_position"]
        indexes = [
            models.Index(fields=['corp_code'], name='executives_corp_code_idx'),
            models.Index(fields=['code'], name='executives_code_idx'),
        ]


class BoardMembers(TimeStampMixin):
    code = models.ForeignKey(
        'BasicInfo'
        , related_name='board_members'
        , on_delete=models.PROTECT
        , to_field='code'
        , help_text='종목코드'
    )
    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    term_name = models.CharField(max_length=10, help_text='기간명')
    member_name = models.CharField(max_length=20, help_text='이사회 멤버 이름')
    member_job = models.CharField(null=True, max_length=50, help_text="업무")
    member_birth_date = models.CharField(null=True, max_length=20, help_text="생년월일")
    member_sex = models.CharField(null=True, max_length=1, help_text="성별")
    member_status = models.CharField(null=True, max_length=20, help_text="상태")
    member_office_term = models.CharField(null=True, max_length=40, help_text="임기 기간")
    member_office_end = models.CharField(null=True, max_length=20, help_text="임기 종료일")

    class Meta:
        db_table = 'board_members'
        unique_together = ["code", "term_name", "member_name", "member_birth_date", "member_job", "member_sex",
                           "member_status"]
        indexes = [
            models.Index(fields=['corp_code'], name='board_members_corp_code_idx'),
            models.Index(fields=['code'], name='board_members_code_idx'),
        ]


class ServiceMentionCounts(TimeStampMixin):
    class TermType(models.TextChoices):
        D = "d", "일"
        W = "w", "주"
        M = "m", "월"
        Q = "q", "분기"
        H = "h", "반기"
        F = "f", "임의의 기간"

    keyword = models.ForeignKey(
        'SocialKeywords'
        # , related_name='mention_counts'
        , on_delete=models.PROTECT
        , to_field='id'
        , help_text='검색 키워드'
    )
    term_type = models.CharField(
        max_length=10,
        choices=TermType.choices,
        default=TermType.D,
        help_text='집계 기간 단위 : d(일), w(주), m(월), q(분기), h(반기), f(임의의 기간)'
    )
    term_start = models.CharField(max_length=10, help_text='기간 시작일')
    term_end = models.CharField(max_length=10, help_text='기간 종료일')
    community_count = models.IntegerField(help_text='커뮤니티 언급량')
    insta_count = models.IntegerField(help_text='인스타 언급량')
    blog_count = models.IntegerField(help_text='블로그 언급량')
    news_count = models.IntegerField(help_text='뉴스 언급량')
    twitter_count = models.IntegerField(help_text='트위터 언급량')
    count_sum = models.IntegerField(help_text='언급량 합')

    class Meta:
        db_table = 'service_mention_counts'
        unique_together = ["keyword", "term_type", "term_start", "term_end"]
        indexes = [
            # models.Index(fields=['corp_code'], name='mention_counts_corp_code_idx'),
            # models.Index(fields=['term_type'], name='mention_counts_term_type_idx'),
            # models.Index(fields=['corp_code', 'subject_name', 'this_term_name'], name='stock_fin_corp_sub_term_idx'),
        ]


class ServiceConnectionWords(TimeStampMixin):
    class TermType(models.TextChoices):
        D = "d", "일"
        W = "w", "주"
        M = "m", "월"
        Q = "q", "분기"
        H = "h", "반기"
        F = "f", "임의의 기간"

    keyword = models.ForeignKey(
        'SocialKeywords'
        # , related_name='mention_counts'
        , on_delete=models.PROTECT
        , to_field='id'
        , help_text='검색 키워드'
    )
    term_type = models.CharField(
        max_length=10,
        choices=TermType.choices,
        default=TermType.D,
        help_text='집계 기간 단위 : d(일), w(주), m(월), q(분기), h(반기), f(임의의 기간)'
    )
    term_start = models.CharField(max_length=10, help_text='기간 시작일')
    term_end = models.CharField(max_length=10, help_text='기간 종료일')
    word = models.CharField(max_length=50, help_text='단어')
    word_count = models.IntegerField(help_text='단어 수')
    rank = models.IntegerField(help_text='단어 수 순위')
    category1 = models.CharField(max_length=100, help_text='카테고리(대분류)')
    category2 = models.CharField(max_length=100, help_text='카테고리(소분류)')

    class Meta:
        db_table = 'service_connection_words'
        unique_together = ["keyword", "term_type", "term_start", "term_end", "word"]
        indexes = [
            # models.Index(fields=['corp_code'], name='connection_words_corp_code_idx'),
            # models.Index(fields=['term_type'], name='connection_words_term_type_idx'),
            # models.Index(fields=['corp_code', 'subject_name', 'this_term_name'], name='stock_fin_corp_sub_term_idx'),
        ]


class ServicePosNegWords(TimeStampMixin):
    class TermType(models.TextChoices):
        D = "d", "일"
        W = "w", "주"
        M = "m", "월"
        Q = "q", "분기"
        H = "h", "반기"
        F = "f", "임의의 기간"

    class PosNeg(models.TextChoices):
        POS = "pos", "긍정"
        NEG = "neg", "부정"
        NEU = "neu", "중립"

    keyword = models.ForeignKey(
        'SocialKeywords'
        # , related_name='mention_counts'
        , on_delete=models.PROTECT
        , to_field='id'
        , help_text='검색 키워드'
    )
    term_type = models.CharField(
        max_length=10,
        choices=TermType.choices,
        default=TermType.D,
        help_text='집계 기간 단위 : d(일), w(주), m(월), q(분기), h(반기), f(임의의 기간)'
    )
    term_start = models.CharField(max_length=10, help_text='기간 시작일')
    term_end = models.CharField(max_length=10, help_text='기간 종료일')
    word = models.CharField(max_length=50, help_text='단어')
    word_count = models.IntegerField(help_text='단어 수')
    rank = models.IntegerField(help_text='단어 수 순위')
    pos_neg = models.CharField(
        max_length=10,
        choices=PosNeg.choices,
        default=PosNeg.NEU,
        help_text='긍/부정 : pos(긍정), neg(부정), neu(중립)'
    )
    property = models.CharField(max_length=100, help_text='속성')

    class Meta:
        db_table = 'service_pos_neg_words'
        unique_together = ["keyword", "term_type", "term_start", "term_end", "word"]
        indexes = [
            # models.Index(fields=['corp_code'], name='pos_neg_words_corp_code_idx'),
            # models.Index(fields=['term_type'], name='pos_neg_words_term_type_idx'),
            # models.Index(fields=['corp_code', 'subject_name', 'this_term_name'], name='stock_fin_corp_sub_term_idx'),
        ]
