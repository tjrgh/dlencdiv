from django.db import models

# Create your models here.
from django.db import models
from ubold.common.models import TimeStampMixin


class CorpCodeData(TimeStampMixin):
    """
    DART 회사 고유번호
    """
    corp_code = models.CharField(max_length=9, unique=True, help_text='DART 고유번호')
    corp_name = models.CharField(max_length=200, help_text='정식 회사명칭')
    stock_code = models.CharField(max_length=7, blank=True, default=' ', help_text='주식 종목코드')
    modify_date = models.CharField(max_length=8, help_text='기업개황정보 최종변경일자')

    class Meta:
        db_table = 'dart_corp_code_data'
        indexes = [
            models.Index(fields=['stock_code'], name='corp_basic_stock_code_idx')
        ]


class DartSearchData(TimeStampMixin):
    """DartSearchData
    DART 검색 api 결과 리스트"""

    class CorpType(models.TextChoices):
        """
        법인구분 enum
        """
        Y = 'Y', '유가'
        K = 'K', '코스닥'
        N = 'N', '코넥스'
        E = 'E', '기타'

    class DataType(models.TextChoices):
        """
        공시유형 enum
        """
        A = 'A', '정기공시'
        B = 'B', '주요사항보고'
        C = 'C', '발행공시'
        D = 'D', '지분공시'
        E = 'E', '기타공시'
        F = 'F', '외부감사관련'
        G = 'G', '펀드공시'
        H = 'H', '자산유동화'
        I = 'I', '거래소공시'
        J = 'J', '공정위공시'
        Z = 'Z', '없음'

    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    corp_name = models.CharField(max_length=200, help_text='정식 회사명칭')
    stock_code = models.CharField(max_length=7, blank=True, default=' ', help_text='주식 종목코드')
    corp_type = models.CharField(
        max_length=10,
        choices=CorpType.choices,
        default=CorpType.Y,
        help_text='법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)'
    )
    data_type = models.CharField(
        max_length=10,
        choices=DataType.choices,
        default=DataType.Z,
        help_text='공시유형'
    )
    title = models.CharField(max_length=300, help_text='제목')
    receipt_no = models.CharField(max_length=14, help_text='접수번호')
    rm = models.CharField(max_length=10, blank=True, default=' ', help_text='비고')
    contents = models.TextField(help_text='보고서 원본 내용 xml or html')
    upload_name = models.CharField(max_length=100, help_text='제출 인명')
    data_date = models.DateField(null=True, help_text='데이터 날짜')

    class Meta:
        db_table = 'dart_search_data'
        indexes = [
            models.Index(fields=['corp_code', 'title'], name='dart_search_data_code_title'),
            models.Index(fields=['corp_name', 'title'], name='dart_search_data_name_title'),
            models.Index(fields=['corp_code', '-data_date'], name='dart_search_data_code_date'),
            models.Index(fields=['corp_name', '-data_date'], name='dart_search_data_name_date'),
        ]


class CorpBasicData(TimeStampMixin):
    """
    DART 기업 개황정보
    """

    class CorpType(models.TextChoices):
        """
        법인구분 enum
        """
        Y = 'Y', '유가'
        K = 'K', '코스닥'
        N = 'N', '코넥스'
        E = 'E', '기타'

    corp_code = models.CharField(max_length=9, unique=True, help_text='DART 고유번호')
    corp_name = models.CharField(max_length=200, help_text='정식 회사명칭')
    corp_name_eng = models.CharField(max_length=255, help_text='영문 정식 회사명칭')
    stock_name = models.CharField(max_length=100, help_text='종목명(상장사) 또는 약식명칭(기타법인)')
    stock_code = models.CharField(max_length=7, blank=True, default=' ', help_text='주식 종목코드')
    ceo_name = models.CharField(max_length=300, help_text='대표자명')
    corp_type = models.CharField(
        max_length=10,
        choices=CorpType.choices,
        default=CorpType.Y,
        help_text='법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)'
    )
    corp_reg_number = models.CharField(max_length=13, help_text='법인등록번호')
    business_reg_number = models.CharField(max_length=10, help_text='사업자등록번호')
    address = models.CharField(max_length=200, blank=True, default=' ', help_text='주소')
    homepage = models.CharField(max_length=200, blank=True, default=' ', help_text='홈페이지')
    ir_homepage = models.CharField(max_length=200, blank=True, default=' ', help_text='IR홈페이지')
    phone_number = models.CharField(max_length=30, help_text='전화번호')
    fax_number = models.CharField(max_length=30, help_text='팩스번호')
    industry_code = models.CharField(max_length=20, help_text='업종코드')
    est_date = models.CharField(max_length=8, help_text='설립일(yyyyMMdd)')
    acc_month = models.CharField(max_length=2, help_text='결산월(MM)')

    class Meta:
        db_table = 'dart_corp_basic_data'
        indexes = [
            models.Index(fields=['corp_code'], name='corp_basic_data_corp_code')
        ]


class IssueIncDecStatus(TimeStampMixin):
    """
    증자(감자)현황 보고서
    """

    class CorpType(models.TextChoices):
        """
        법인구분 enum
        """
        Y = 'Y', '유가'
        K = 'K', '코스닥'
        N = 'N', '코넥스'
        E = 'E', '기타'

    class ReportCode(models.TextChoices):
        """
        보고서 코드 enum
        """
        Q1 = '11013', '1분기'
        Q2 = '11012', '반기'
        Q3 = '11014', '3분기'
        Q4 = '11011', '사업보고서'

    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    business_year = models.CharField(max_length=4, help_text='사업년도(yyyy)')
    report_code = models.CharField(
        max_length=10,
        choices=ReportCode.choices,
        default=ReportCode.Q4,
        help_text='보고서코드 : 11013:1분기, 11012:반기, 11014:3분기, 11011: 사업'
    )
    receipt_number = models.CharField(max_length=14, help_text='접수번호')
    corp_type = models.CharField(
        max_length=10,
        choices=CorpType.choices,
        default=CorpType.Y,
        help_text='법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)'
    )
    corp_name = models.CharField(max_length=200, help_text='법인명')
    stock_issue_decrease_date = models.CharField(max_length=15, help_text='주식발행 감소일자')
    issue_decrease_style = models.CharField(max_length=15, help_text='발행 감소 형태')
    issue_decrease_stock_kind = models.CharField(max_length=15, help_text='발행 감소 주식 종류')
    issue_decrease_quantity = models.CharField(max_length=15, help_text='발행 감소 수량')
    issue_decrease_mstvdv_face_value_amount = models.CharField(max_length=15, help_text='발행 감소 주당 액면 가액')
    issue_decrease_mstvdv_amount = models.CharField(max_length=15, help_text='발행 감소 주당 가액')

    class Meta:
        db_table = 'dart_issue_inc_dec_status'
        indexes = [
            models.Index(fields=['corp_code'], name='issue_status_corp_code_idx')
        ]


class StockDividend(TimeStampMixin):
    """
    배당에 관한 사항
    """
    class CorpType(models.TextChoices):
        """
        법인구분 enum
        """
        Y = 'Y', '유가'
        K = 'K', '코스닥'
        N = 'N', '코넥스'
        E = 'E', '기타'

    class ReportCode(models.TextChoices):
        """
        보고서 코드 enum
        """
        Q1 = '11013', '1분기'
        Q2 = '11012', '반기'
        Q3 = '11014', '3분기'
        Q4 = '11011', '사업보고서'

    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    business_year = models.CharField(max_length=4, help_text='사업년도(yyyy)')
    report_code = models.CharField(
        max_length=10,
        choices=ReportCode.choices,
        default=ReportCode.Q4,
        help_text='보고서코드 : 11013:1분기, 11012:반기, 11014:3분기, 11011: 사업'
    )
    receipt_number = models.CharField(max_length=14, help_text='접수번호')
    corp_type = models.CharField(
        max_length=10,
        choices=CorpType.choices,
        default=CorpType.Y,
        help_text='법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)'
    )
    corp_name = models.CharField(max_length=200, help_text='법인명')
    se = models.CharField(max_length=15, help_text='구분')
    stock_kind = models.CharField(max_length=15, help_text='주식 종류')
    this_term = models.CharField(max_length=15, help_text='당기')
    former_term = models.CharField(max_length=15, help_text='전기')
    lw_former_term = models.CharField(max_length=15, help_text='전전기')

    class Meta:
        db_table = 'dart_stock_dividend'
        indexes = [
            models.Index(fields=['corp_code'], name='stock_dividend_corp_code_idx')
        ]


class TreasuryStockStatus(TimeStampMixin):
    """
    자기주식 취득 및 처분 현황
    """
    class CorpType(models.TextChoices):
        """
        법인구분 enum
        """
        Y = 'Y', '유가'
        K = 'K', '코스닥'
        N = 'N', '코넥스'
        E = 'E', '기타'

    class ReportCode(models.TextChoices):
        """
        보고서 코드 enum
        """
        Q1 = '11013', '1분기'
        Q2 = '11012', '반기'
        Q3 = '11014', '3분기'
        Q4 = '11011', '사업보고서'

    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    business_year = models.CharField(max_length=4, help_text='사업년도(yyyy)')
    report_code = models.CharField(
        max_length=10,
        choices=ReportCode.choices,
        default=ReportCode.Q4,
        help_text='보고서코드 : 11013:1분기, 11012:반기, 11014:3분기, 11011: 사업'
    )
    receipt_number = models.CharField(max_length=14, help_text='접수번호')
    corp_type = models.CharField(
        max_length=10,
        choices=CorpType.choices,
        default=CorpType.Y,
        help_text='법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)'
    )
    corp_name = models.CharField(max_length=200, help_text='법인명')
    acquires_method1 = models.CharField(max_length=20, help_text='취득방법 대분류. 배당가능이익범위 이내 취득, 기타취득, 총계 등')
    acquires_method2 = models.CharField(max_length=20, help_text='취득방법 중분류. 직접취득, 신탁계약에 의한취득, 기타취득, 총계 등')
    acquires_method3 = models.CharField(
        max_length=20
        , help_text='취득방법 소분류. 장내직접취득, 장외직접취득, 공개매수, 주식매수청구권행사, 수탁자보유물량, 현물보유량, 기타취득, 소계, 총계 등'
    )
    stock_kind = models.CharField(max_length=15, help_text='주식 종류')
    basis_quantity = models.CharField(max_length=15, help_text='기초 수량')
    change_quantity_acquires = models.CharField(max_length=15, help_text='변동 수량 취득')
    change_quantity_disposal = models.CharField(max_length=15, help_text='변동 수량 처분')
    change_quantity_incinerate = models.CharField(max_length=15, help_text='변동 수량 소각')
    term_end_quantity = models.CharField(max_length=15, help_text='기말 수량')
    rm = models.CharField(max_length=250, help_text='비고')

    class Meta:
        db_table = 'dart_treasury_stock_status'
        indexes = [
            models.Index(fields=['corp_code'], name='t_stock_status_corp_code_idx')
        ]


class LargestShareholderStatus(TimeStampMixin):
    """
    최대주주 현황
    """
    class CorpType(models.TextChoices):
        """
        법인구분 enum
        """
        Y = 'Y', '유가'
        K = 'K', '코스닥'
        N = 'N', '코넥스'
        E = 'E', '기타'

    class ReportCode(models.TextChoices):
        """
        보고서 코드 enum
        """
        Q1 = '11013', '1분기'
        Q2 = '11012', '반기'
        Q3 = '11014', '3분기'
        Q4 = '11011', '사업보고서'

    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    business_year = models.CharField(max_length=4, help_text='사업년도(yyyy)')
    report_code = models.CharField(
        max_length=10,
        choices=ReportCode.choices,
        default=ReportCode.Q4,
        help_text='보고서코드 : 11013:1분기, 11012:반기, 11014:3분기, 11011: 사업'
    )
    receipt_number = models.CharField(max_length=14, help_text='접수번호')
    corp_type = models.CharField(
        max_length=10,
        choices=CorpType.choices,
        default=CorpType.Y,
        help_text='법인구분 : Y(유가), K(코스닥), N(코넥스), E(기타)'
    )
    corp_name = models.CharField(max_length=200, help_text='법인명')
    name = models.CharField(max_length=100, help_text='성명')
    relate = models.CharField(max_length=100, help_text='관계')
    stock_kind = models.CharField(max_length=15, help_text='주식 종류')
    basis_possession_stock_co = models.CharField(max_length=15, help_text='기초 소유 주식 수')
    basis_possession_stock_quota_rate = models.CharField(max_length=15, help_text='기초 소유 주식 지분 율')
    term_end_possession_stock_co = models.CharField(max_length=15, help_text='기말 소유 주식 수')
    term_end_possession_stock_quota_rate = models.CharField(max_length=15, help_text='기말 소유 주식 지분 율')
    rm = models.CharField(max_length=250, help_text='비고')

    class Meta:
        db_table = 'dart_largest_shareholder_status'
        indexes = [
            models.Index(fields=['corp_code'], name='holder_status_corp_code_idx')
        ]


class FinancialStatement(TimeStampMixin):

    class ReportCode(models.TextChoices):
        """
        보고서 코드 enum
        """
        Q1 = '11013', '1분기'
        Q2 = '11012', '반기'
        Q3 = '11014', '3분기'
        Q4 = '11011', '사업보고서'

    class SubjectCode(models.TextChoices):
        """
        재무제표 구분 enum
        """
        BS = 'BS', '재무상태표'
        IS = 'IS', '손익계산서'
        CIS = 'CIS', '포괄손익계산서'
        CF = 'CF', '현금흐름표'
        SCE = 'SCE', '자본변동표'

    corp_code = models.CharField(max_length=9, help_text='DART 고유번호')
    receipt_no = models.CharField(max_length=14, help_text='접수번호')
    report_code = models.CharField(
        max_length=10,
        choices=ReportCode.choices,
        default=ReportCode.Q4,
        help_text='보고서코드 : 11013:1분기, 11012:반기, 11014:3분기, 11011: 사업'
    )
    business_year = models.CharField(max_length=5, help_text='사업년도')
    subject_div = models.CharField(
        max_length=10,
        choices=SubjectCode.choices,
        default=SubjectCode.BS,
        help_text='재무제표 구분 : BS:재무상태표, IS:손익계산서, CIS:포괄손익계산서, CF: 현금흐름표, SCE:자본변동표'
    )
    subject_name = models.CharField(max_length=10, help_text='재무제표명')
    account_id = models.CharField(max_length=500, help_text='XBRL 표준계정 ID')
    account_name = models.CharField(max_length=100, help_text='계정명')
    account_detail = models.CharField(max_length=200, help_text='계정 상세명칭')
    this_term_name = models.CharField(max_length=100, help_text='당기 명')
    this_term_amount = models.DecimalField(
        max_digits=21, decimal_places=2, help_text='당기 금액'
    )
    this_term_add_amount = models.DecimalField(
        max_digits=21, decimal_places=2, help_text='당기 누적 금액'
    )
    former_term_name = models.CharField(max_length=100, help_text='전기 명')
    former_term_amount = models.DecimalField(
        max_digits=21, decimal_places=2, help_text='전기 금액'
    )
    former_quota_term_name = models.CharField(max_length=100, help_text='전기(분/반기) 명')
    former_quota_term_amount = models.DecimalField(
        max_digits=21, decimal_places=2, help_text='전기(분/반기) 금액'
    )
    former_term_add_amount = models.DecimalField(
        max_digits=21, decimal_places=2, help_text='전기 누적 금액'
    )
    before_former_term_name = models.CharField(max_length=100, help_text='전전기 명')
    before_former_term_amount = models.DecimalField(
        max_digits=21, decimal_places=2, help_text='전전기 금액'
    )
    ordering = models.IntegerField(help_text='계정과목 정렬순서')

    class Meta:
        db_table = 'dart_financial_statement'
        indexes = [
            models.Index(fields=['corp_code'], name='financial_corp_code_idx'),
            models.Index(fields=['subject_name'], name='financial_subject_name_idx'),
        ]
