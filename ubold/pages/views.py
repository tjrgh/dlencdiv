import calendar

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.db.models import Count

from ubold.pages import common_util, price_predict
from ubold.pages.price_predict import StockPricePredict, StockPricePredictService
from ubold.stocks.models import StaffNumber, BoardMemberAverageWage, BoardMemberPersonalWage, SocialKeywords, ServiceMentionCounts, \
    ServicePosNegWords, news_reactions, SocialKeywordGroup
from ubold.dart.models import DartSearchData
from ubold.stocks.models import FinancialStatement, HistoricData, BasicInfo, Dividend, Shareholder, WorkerCountAndPay, BoardMembers

import numpy as np
import pandas as pd
import psycopg2
import datetime

User = get_user_model()

keyword_group = {
    "financial":{
        "city_bank": ["신한은행", "KB국민은행", "우리은행", "NH농협은행", "하나은행"],
        "local_bank": ["대구은행", "부산은행", "광주은행", "전북은행", "경남은행", "제주은행"],
        "non_face_to_face_bank": ["카카오뱅크", "K뱅크", "토스"],
        "stock":["미래에셋증권", "KB증권", "NH투자증권", "삼성증권", "한화투자증권", "SK증권", "한국투자증권", "대신증권", "키움증권", "신한금융투자", "하나금융투자", "메리츠증권"],
        "life_insurance":["삼성생명", "한화생명", "푸르덴셜생명", "교보생명", "HN농협생명", "미래에셋생명", "오렌지라이프", "신한생명", "동양생명", "흥국생명"],
        "fire_insurance":["삼성화재", "동부화재", "현대해상", "KB손해보험", "메리츠화재", "흥국화재"],
        "capital": ["KB캐피탈", "신한캐피탈", "하나캐피탈", "우리금융캐피탈", "메리츠캐피탈", "현대캐피탈", "NH농협캐피탈", "산은캐피탈"],
        "card":["롯데카드", "비씨카드", "삼성카드", "신한카드", "우리카드", "하나카드", "현대카드", "KB국민카드", "NH농협카드"],

    },
    "circulation":{
        "department_store":["롯데백화점", "현대백화점", "신세계백화점"],
        "market":["이마트", "롯데마트", "홈플러스", "트레이더스", "코스트코"],
        "convenience":["세븐일레븐", "GS25", "CU", "이마트24", "미니스톱"],
        "ecommerce":["쿠팡", "위메프", "옥션", "11번가", "G마켓", "SSG닷컴", "마켓컬리", "인터파크", "티몬"            ],
        "parcel":["CJ대한통운", "한진택배", "롯데글로벌로직스", "로젠택배"]
    },
    "car":{
        "domesticCompany":["현대차", "기아", "쌍용차", "르노삼성", "제네시스"],
        "foreignCompany":["메르세데스벤츠", "BMW", "폭스바겐", " 토요타", "볼보", "아우디", "포르쉐", "페라리", "테슬라", "GM", "포드", "렉서스", "벤츠"],
        "car":["G80", "그랜저", "소나타", "아반떼", "K8", "K5", "G70", "G90", "K3", "스팅어", "K9"],
        "suv":["GV60", "GV70", "GV80", "쏘렌토", "카니발", "팰리세이드", "싼타페", "모하비", "스포티지", "니로", "셀토스"],
        "imported":["벤츠E300", "벤츠d", "BMW 5시리즈", "BMW 3시리즈", "아우디 A6", "렉서스ES", "벤츠C", "토요타 캠리", "벤츠 GLE", "벤츠 GLB"],
        "electric":["모델S", "모델Y", "모델X", "모델3", "아이오닉5", "EV6", "볼트EV", "니로EV"],
    },
    "food":{
        "company":["농심", "삼양식품", "오뚜기", "야쿠르트", "동원F", "CJ제일제당", "동원", "풀무원", "하이트진로", "롯데칠성음료", "빙그레", "해태제과", "오리온", "매일유업", "남양유업"],
        "ramen":["신라면", "진라면", "안성탕면", "불닭볶음면", "짜파게티", "짜왕", "팔도비빔면"],
        "rice":["햇반", "오뚜기밥"],
        "soju":["참이슬", "처음처럼"],
        "beer":["테라", "카스", "클라우드", "라거"],
        "franchise":["BBQ", "BHC", "교촌", "깐부", "맘스터치", "버거킹", "롯데리아", "피자헛", "도미노"],
    },
    "groupCompany":{
        "majorGroup":["삼성그룹", "현대차그룹", "SK그룹", "롯데그룹", "포스코그룹", "농협", "한화그룹", "GS그룹", "LG그룹", "현대중공업그룹"],
    }


}

class CustomView(LoginRequiredMixin, TemplateView):
    pass

class PriceAnalysisView(LoginRequiredMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = datetime.datetime.today() - datetime.timedelta(days=7)
        data = DartSearchData.objects.filter(data_date=today.date()).order_by('-created_at')

        context['now'] = today
        context['darts'] = data

        return context

brand_keyword_list = [
        "e편한세상",
        "꿈에그린",
        "더샵",
        "디에이치",
        "더플래티넘",
        "데시앙",
        "동문굿모닝힐",
        "동원베네스트",
        "래미안",
        "롯데캐슬",
        "리슈빌",
        "반도유보라",
        "베르디움",
        "벽산블루밍",
        "삼부르네상스",
        "서희스타힐스",
        "센트레빌",
        "스위첸",
        "아이파크",
        "아크로",
        "금호어울림",
        "SK뷰",
        "우미린",
        "위브",
        "자이",
        "코아루",
        "포레나",
        "푸르지오",
        "하늘채",
        "한라비발디",
        "해링턴플레이스",
        "해모르",
        "호반써밋",
        "힐스테이트",
    ]
include_keyword_set_list = {
    "브랜드":{
       "브랜드": {""},
    },
    "지향점":{
        "기술력":{"기술력"},
        "디자인": {"디자인"},
        "살기좋은": {"살기좋은"},
        "선호하는": {"선호하는"},
        "스마트": {"스마트"},
        "신뢰": {"신뢰"},
        "입지좋은": {"입지좋은"},
        "추천하는": {"추천하는"},
        "친환경": {"친환경"},
        "투자가치": {"투자가치"},
        "품질좋은": {"품질좋은"},
        "라이프스타일": {"라이프스타일"},
        "프리미엄": {"프리미엄"},
    },
    "2021주요트렌드": {
        "친환경": {"친환경"},
        "라이프스타일": {"라이프스타일"},
        "설계": {"설계","평면"},
        "디자인": {"디자인"},
        "커뮤니티(컨시어지)": {"컨시어지","재택","재택근무","원격교육","원격수업"},
        "문화": {"문화"},
        "코로나": {"코로나"},
        "경험": {"경험","재택"},
        "수요": {"수요"},
        "가치": {"가치"},
        "인테리어": {"인테리어","벽체","바닥재","마감재"},
        "공간": {"가변","펜트리","멀티룸"},
    },
    "2022예상트렌드":{
        "인공지능": {"인공지능"},
        "지능화": {"홈네트워크","모니터링","공조","제어"},
        "메타버스": {"메타버스"},
        "안전": {"안전","보안","지하화"},
        "커뮤니티(컨시어지)": {"컨시어지","재택","재택근무","원격교육","원격수업"},
        "스몰": {"소형","초소형"},
        "재생": {"리페어"},
        "자연": {"로컬","친환경"},
        "럭셔리": {"럭셔리","대형평형"},
        "개인화": {"독립공간","유해요소차단"},
    },
    "경제특성": {
        "가격상승": {"가격상승"},
        "개발계획": {"개발계획"},
        "미래가치": {"미래가치"},
        "투자가치": {"투자가치"},
        "주거비용": {"주거비용"},
    },
    "구조특성": {
        "인테리어": {"인테리어","벽체","바닥재","마감재"},
        "소음": {"소음감소","층간소음저감","소음저감"},
        "채광": {"채광","남향"},
        "환기": {"환기","에어샤워","공기정화"},
        "평면": {"거실","안방","베란다","화장실","주방","알파룸"},
    },
    "환경특성": {
        "개발": {"재건축","재개발","호재","개발"},
        "주변": {"공원","관공서","녹지","근린시설","병원","마트","숲세권","스세권","올세권","다세권"},
        "커뮤니티(컨시어지)": {"커뮤니티","컨시어지","헬스장","운동","사우나","수영장","볼링장","극장","게스트하우스","도서관","카페","라운지","돌봄"},
        "교통": {"대중교통","전철","지하철","교통","역세권"},
        "교육": {"교육","학군","학원","초중고","초품아"},
    },

}
# include_keyword_set_list2 = {
#     "브랜드":{
#        "브랜드": {"and_or": "and", "include_list": {"아파트"}},
#     },
#     "지향점":{
#         "기술력":{"and_or": "and", "include_list": {"기술력", "아파트"}},
#         "디자인": {"and_or": "and", "include_list": {"디자인"}},
#         "살기좋은": {"and_or": "and", "include_list": {"살기좋은"}},
#         "선호하는": {"and_or": "and", "include_list": {"선호하는"}},
#         "스마트": {"and_or": "and", "include_list": {"스마트"}},
#         "신뢰": {"and_or": "and", "include_list": {"신뢰"}},
#         "입지좋은": {"and_or": "and", "include_list": {"입지좋은"}},
#         "추천하는": {"and_or": "and", "include_list": {"추천하는"}},
#         "친환경": {"and_or": "and", "include_list": {"친환경"}},
#         "투자가치": {"and_or": "and", "include_list": {"투자가치"}},
#         "품질좋은": {"and_or": "and", "include_list": {"품질좋은"}},
#         "라이프스타일": {"and_or": "and", "include_list": {"라이프스타일"}},
#         "프리미엄": {"and_or": "and", "include_list": {"프리미엄"}},
#     },
#     "2021주요트렌드": {
#         "친환경": {"and_or": "and", "include_list": {"친환경"}},
#         "라이프스타일": {"and_or": "and", "include_list": {"라이프스타일"}},
#         "설계": {"and_or": "and", "include_list": {"설계","평면"}},
#         "디자인": {"and_or": "and", "include_list": {"디자인"}},
#         "커뮤니티(컨시어지)": {"and_or": "and", "include_list": {"컨시어지","재택","재택근무","원격교육","원격수업"}},
#         "문화": {"and_or": "and", "include_list": {"문화"}},
#         "코로나": {"and_or": "and", "include_list": {"코로나"}},
#         "경험": {"and_or": "and", "include_list": {"경험","재택"}},
#         "수요": {"and_or": "and", "include_list": {"수요"}},
#         "가치": {"and_or": "and", "include_list": {"가치"}},
#         "인테리어": {"and_or": "and", "include_list": {"인테리어","벽체","바닥재","마감재"}},
#         "공간": {"and_or": "and", "include_list": {"가변","펜트리","멀티룸"}},
#     },
#     "2022예상트렌드":{
#         "인공지능": {"and_or": "and", "include_list": {"인공지능"}},
#         "지능화": {"and_or": "and", "include_list": {"홈네트워크","모니터링","공조","제어"}},
#         "메타버스": {"and_or": "and", "include_list": {"메타버스"}},
#         "안전": {"and_or": "and", "include_list": {"안전","보안","지하화"}},
#         "커뮤니티(컨시어지)": {"and_or": "and", "include_list": {"컨시어지","재택","재택근무","원격교육","원격수업"}},
#         "스몰": {"and_or": "and", "include_list": {"소형","초소형"}},
#         "재생": {"and_or": "and", "include_list": {"리페어"}},
#         "자연": {"and_or": "and", "include_list": {"로컬","친환경"}},
#         "럭셔리": {"and_or": "and", "include_list": {"럭셔리","대형평형"}},
#         "개인화": {"and_or": "and", "include_list": {"독립공간","유해요소차단"}},
#     },
#     "경제특성": {
#         "가격상승": {"and_or": "and", "include_list": {"가격상승"}},
#         "개발계획": {"and_or": "and", "include_list": {"개발계획"}},
#         "미래가치": {"and_or": "and", "include_list": {"미래가치"}},
#         "투자가치": {"and_or": "and", "include_list": {"투자가치"}},
#         "주거비용": {"and_or": "and", "include_list": {"주거비용"}},
#     },
#     "구조특성": {
#         "인테리어": {"and_or": "and", "include_list": {"인테리어","벽체","바닥재","마감재"}},
#         "소음": {"and_or": "and", "include_list": {"소음감소","층간소음저감","소음저감"}},
#         "채광": {"and_or": "and", "include_list": {"채광","남향"}},
#         "환기": {"and_or": "and", "include_list": {"환기","에어샤워","공기정화"}},
#         "평면": {"and_or": "and", "include_list": {"거실","안방","베란다","화장실","주방","알파룸"}},
#     },
#     "환경특성": {
#         "개발": {"and_or": "and", "include_list": {"재건축","재개발","호재","개발"}},
#         "주변": {"and_or": "and", "include_list": {"공원","관공서","녹지","근린시설","병원","마트","숲세권","스세권","올세권","다세권"}},
#         "커뮤니티(컨시어지)": {"and_or": "and", "include_list": {"커뮤니티","컨시어지","헬스장","운동","사우나","수영장","볼링장","극장","게스트하우스","도서관","카페","라운지","돌봄"}},
#         "교통": {"and_or": "and", "include_list": {"대중교통","전철","지하철","교통","역세권"}},
#         "교육": {"and_or": "and", "include_list": {"교육","학군","학원","초중고","초품아"}},
#     },
#
# }

# 메뉴 레벨에 해당하는 키워드 목록을 가져와, 그 키워드들에 대한 데이터들을 적절한 형태로 가공하여 페이지로 반환.
class SocialAnalysisView(LoginRequiredMixin, TemplateView):
    lv1 = ""
    lv2 = ""
    start_date = ""
    end_date = ""
    keyword_group_code = ""

    keyword = {
        "brandImageKeyword": [
            "기술력",
            "디자인",
            "살기좋은",
            "선호하는",
            "스마트",
            "신뢰",
            "입지좋은",
            "추천하는",
            "친환경",
            "투자가치",
            "품질좋은",
            "프리미엄",
        ],
        "economicCharacter":[
            "가격상승", "개발계획", "미래가치", "투자가치", "주거비용",
        ],
        "structureCharacter": [
            "마감재",
            "벽체",
            "인테리어",
            "바닥재",
            "층간소음",
            "채광",
            "환기",
            "거실",
            "안방",
            "베란다",
            "화장실",
            "주방",
            "알파룸",
        ],
        "environmentCharacter": [
            "재건축",
            "호재",
            "재개발",
            "공원",
            "관공서",
            "녹지",
            "병원",
            "마트",
            "커뮤니티시설",
            "헬스장",
            "운동",
            "커뮤니티",
            "사우나",
            "대중교통",
            "전철",
            "지하철",
            "교통",
            "역세권",
            "학군",
            "학교",
            "학원",
            "교육",
            "대학",
        ],
        "mainTrend2021":[
            "친환경",
            "라이프스타일",
            "설계",
            "디자인",
            "커뮤니티",
            "문화",
            "코로나",
            "경험",
            "재택",
            "수요",
            "가치",
            "인테리어",
            "가변",
            "펜트리",
            "멀티룸",
        ],
        "expectedTrend2022":[
            "인공지능",
            "홈네트워크",
            "메타버스",
            "안전",
            "보안",
            "재택",
            "소형",
            "초소형",
            "리페어",
            "로컬",
            "럭셔리",
            "독립공간",
            "유해요소차단",
        ]
    }
    include_keyword = ""


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # url 쿼리 스트링 가져오기.
        if (self.request.GET.get("lv1", None) != None) & (self.request.GET.get("lv2", None) != None):
            self.lv1 = self.request.GET.get("lv1")
            self.lv2 = self.request.GET.get("lv2")
        else:
            self.lv1 = "지향점"
            self.lv2 = "기술력"

        if (self.request.GET.get("startDate", None) != None) & (self.request.GET.get("endDate", None) != None):
            self.start_date = self.request.GET.get("startDate")
            self.end_date = self.request.GET.get("endDate")
        else:
            self.start_date = "2021-01-01"
            self.end_date = datetime.date.today().isoformat()

        # social_keyword_group_id = SocialKeywordGroup.objects.filter(code=self.keyword_group_code).get().id
        # keyword_list = pd.DataFrame(list(SocialKeywords.objects.filter(keyword_group=social_keyword_group_id, is_deleted=False, is_followed=True).values()))

        # lv에 해당하는 키워드 목록 가져오기.
        keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=brand_keyword_list, is_deleted=False, is_followed=True).values()))
        keyword_list = pd.DataFrame()
        for idx in keyword_df.index:
            keyword_row = keyword_df.loc[idx]

            # include_keyword_set = {}
            # if include_keyword_set_list[self.lv1][self.lv2]["and_or"] == "and":
            #     include_keyword_set = set(keyword_row["and_include_keyword_list"].split("\\"))
            # elif include_keyword_set_list[self.lv1][self.lv2]["and_or"] == "or":
            #     include_keyword_set = set(keyword_row["or_include_keyword_list"].split("\\"))
            include_keyword_set = set(keyword_row["or_include_keyword_list"].split("\\"))
            # if include_keyword_set == include_keyword_set_list[self.lv1][self.lv2]["include_list"]:
            if include_keyword_set == include_keyword_set_list[self.lv1][self.lv2]:
                keyword_list = keyword_list.append(keyword_row)
            # for include_keyword in include_keyword_set_list[self.include_keyword]:
            #     if (include_keyword in include_keyword_list) & (len(include_keyword_list) == 2):
            #         keyword_list = keyword_list.append(keyword_row)

        # keyword_list = self.keyword[lv1][lv2]# 해당하는 키워드 목록
        # keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=keyword_list, is_deleted=False, is_followed=True).values()))

        # 각 키워드에 대해 db로부터 언급량 데이터 가져옴.
        temp_mention_count_dict = {}
        for idx in keyword_list.index:
            temp_mention_count_df = pd.DataFrame(list(ServiceMentionCounts.objects.filter(
                keyword_id=keyword_list["id"][idx], term_start__gt=self.start_date, term_end__lt=self.end_date).values())) # 한 키워드에 대한 언급량 데이터 목록.
            temp_mention_count_dict[keyword_list["keyword"][idx]] = temp_mention_count_df


        # 각 키워드의 데이터에 대해, 전체, 커뮤니티별, 인스타별, ... 트위터별로 그래프에 넘겨줄 data series 만들기.
        # 기간에 대해 반복하며 생성.
        # date_diff = datetime(self.end_date) - datetime(self.start_date)

        start_date = datetime.date(int(self.start_date.split("-")[0]), int(self.start_date.split("-")[1]), int(self.start_date.split("-")[2]),)
        end_date = datetime.date(int(self.end_date.split("-")[0]), int(self.end_date.split("-")[1]), int(self.end_date.split("-")[2]),)
        target_date = datetime.date(start_date.year, start_date.month, start_date.day)

        # 기간에 대한 전체 date리스트.
        day_list = []
        while target_date<=end_date:
            day_list.append(calendar.timegm(target_date.timetuple()) * 1000)
            target_date += datetime.timedelta(days=1)

        # 그래프 상에 x축에서 보여줄 date리스트.
        xaxis_day_list = []
        xaxis_term = int((end_date - start_date).days / 10)
        count = 0
        target_date = datetime.date(start_date.year, start_date.month, start_date.day)
        while target_date <= end_date:
            if count == xaxis_term:
                xaxis_day_list.append(calendar.timegm(target_date.timetuple()) * 1000)
                count = 0
            count += 1
            target_date += datetime.timedelta(days=1)

        context["keyword_list"] = brand_keyword_list
        context["mention_data"] = {
            "total_mention": { "name": "전체 언급량 추이"},
            "community_mention": {"name": "커뮤니티 언급량 추이"},
            "insta_mention": {"name": "인스타 언급량 추이"},
            "blog_mention": {"name": "블로그 언급량 추이"},
            "news_mention": {"name": "뉴스 언급량 추이"},
            "twitter_mention": {"name": "트위터 언급량 추이"},
        }
        context["xaxis_day_list"] = xaxis_day_list
        # context["include_keyword_set"] = include_keyword_set_list[self.lv1][self.lv2]["include_list"]
        context["include_keyword_set"] = include_keyword_set_list[self.lv1][self.lv2]
        # and,or에 따라 적용 수정 후
        # context["include_keyword_and_or"] = include_keyword_set_list[self.lv1][self.lv2]["and_or"]
        # context["include_keyword_set"] = include_keyword_set_list[self.lv1][self.lv2]["include_list"]

        return context

def mention_data(request):
    start_date_iso = "2021-01-01"
    end_date_iso = datetime.date.today().isoformat()
    lv1 = ""
    lv2 = ""

    # url 쿼리 스트링 가져오기.
    if (request.GET.get("startDate", None) != None) & (request.GET.get("endDate", None) != None):
        start_date_iso = request.GET.get("startDate")
        end_date_iso = request.GET.get("endDate")

    if (request.GET.get("lv1", None) != None) & (request.GET.get("lv2", None) != None):
        lv1 = request.GET.get("lv1")
        lv2 = request.GET.get("lv2")
    else:
        lv1 = "지향점"
        lv2 = "기술력"

    # lv에 해당하는 키워드 목록 가져오기.
    keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=brand_keyword_list, is_deleted=False, is_followed=True).values()))
    keyword_list = pd.DataFrame()
    for idx in keyword_df.index:
        keyword_row = keyword_df.loc[idx]

        # include_keyword_set = {}
        # if include_keyword_set_list[lv1][lv2]["and_or"] == "and":
        #     include_keyword_set = set(keyword_row["and_include_keyword_list"].split("\\"))
        # elif include_keyword_set_list[lv1][lv2]["and_or"] == "or":
        #     include_keyword_set = set(keyword_row["or_include_keyword_list"].split("\\"))
        include_keyword_set = set(keyword_row["or_include_keyword_list"].split("\\"))
        # if include_keyword_set == include_keyword_set_list[lv1][lv2]["include_list"]:
        if include_keyword_set == include_keyword_set_list[lv1][lv2]:
            keyword_list = keyword_list.append(keyword_row)
        # include_keyword_list = keyword_row["and_include_keyword_list"].split("\\")
        # if (include_keyword in include_keyword_list) & ("아파트" in include_keyword_list) & (len(include_keyword_list) == 2):
        #     keyword_list = keyword_list.append(keyword_row)

    # keyword_list = self.keyword[lv1][lv2]# 해당하는 키워드 목록
    # keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=keyword_list, is_deleted=False, is_followed=True).values()))

    # 각 키워드에 대해 db로부터 언급량 데이터 가져옴.
    temp_mention_count_dict = {}
    for idx in keyword_list.index:
        temp_mention_count_df = pd.DataFrame(list(ServiceMentionCounts.objects.filter(
            keyword_id=keyword_list["id"][idx], term_start__gte=start_date_iso, term_end__lte=end_date_iso).values()))  # 한 키워드에 대한 언급량 데이터 목록.
        temp_mention_count_dict[keyword_list["keyword"][idx]] = temp_mention_count_df

    #


    # lv에 해당하는 키워드 목록 가져오기.
    # keyword_list = keyword_group[lv1][lv2]  # 해당하는 키워드 목록
    # keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=keyword_list, is_deleted=False, is_followed=True).values()))

    # 각 키워드에 대해 db로부터 언급량 데이터 가져옴.
    # temp_mention_count_dict = {}
    # for idx in keyword_df.index:
    #     temp_mention_count_df = pd.DataFrame(list(ServiceMentionCounts.objects.filter(
    #         keyword_id=keyword_df["id"][idx], term_start__gt=start_date_iso, term_end__lt=end_date_iso).values()))  # 한 키워드에 대한 언급량 데이터 목록.
    #     temp_mention_count_dict[keyword_df["keyword"][idx]] = temp_mention_count_df

    # 각 키워드의 데이터에 대해, 전체, 커뮤니티별, 인스타별, ... 트위터별로 그래프에 넘겨줄 data series 만들기.
    # 기간에 대해 반복하며 생성.

    start_date_datetime = datetime.date(int(start_date_iso.split("-")[0]), int(start_date_iso.split("-")[1]), int(start_date_iso.split("-")[2]), )
    end_date_datetime = datetime.date(int(end_date_iso.split("-")[0]), int(end_date_iso.split("-")[1]), int(end_date_iso.split("-")[2]), )
    target_date_datetime = datetime.date(start_date_datetime.year, start_date_datetime.month, start_date_datetime.day)

    # 기간에 대한 전체 date리스트.
    day_list = []
    while target_date_datetime <= end_date_datetime:
        day_list.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
        target_date_datetime += datetime.timedelta(days=1)

    # 그래프 상에 x축에서 보여줄 date리스트.
    xaxis_day_list = []
    xaxis_term = int((end_date_datetime - start_date_datetime).days / 10)
    count = 0
    target_date_datetime = datetime.date(start_date_datetime.year, start_date_datetime.month, start_date_datetime.day)
    while target_date_datetime <= end_date_datetime:
        if count == xaxis_term:
            xaxis_day_list.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
            count = 0
        count += 1
        target_date_datetime += datetime.timedelta(days=1)

    # 전체 언급량.
    total_mention = {}
    community_mention = {}
    insta_mention = {}
    blog_mention = {}
    news_mention = {}
    twitter_mention = {}

    total_mention_sum = {}
    community_mention_sum = {}
    insta_mention_sum = {}
    blog_mention_sum = {}
    news_mention_sum = {}
    twitter_mention_sum = {}

    for keyword_key, value in temp_mention_count_dict.items():

        if value.empty == True:
            total_mention_sum[keyword_key] = 0
            community_mention_sum[keyword_key] = 0
            insta_mention_sum[keyword_key] = 0
            blog_mention_sum[keyword_key] = 0
            news_mention_sum[keyword_key] = 0
            twitter_mention_sum[keyword_key] = 0
            continue

        total_mention_sum[keyword_key] = int(value["count_sum"].sum())
        community_mention_sum[keyword_key] = int(value["community_count"].sum())
        insta_mention_sum[keyword_key] = int(value["insta_count"].sum())
        blog_mention_sum[keyword_key] = int(value["blog_count"].sum())
        news_mention_sum[keyword_key] = int(value["news_count"].sum())
        twitter_mention_sum[keyword_key] = int(value["twitter_count"].sum())

        # timestamp값, 각 타입에 대한 언급량으로 이루어진 df만들기.
        convertedDf = None
        def convertIsoToTimestamp(iso):
            iso_datetime = common_util.iso_to_datetime(iso)
            return calendar.timegm(iso_datetime.timetuple()) * 1000
        timestamp_series = value["term_start"].apply(convertIsoToTimestamp)

        def convertInt(x):
            return int(x)
        total_mention_series = value["count_sum"].apply(convertInt)
        community_mention_series = value["community_count"].apply(convertInt)
        insta_mention_series = value["insta_count"].apply(convertInt)
        blog_mention_series = value["blog_count"].apply(convertInt)
        news_mention_series = value["news_count"].apply(convertInt)
        twitter_mention_series = value["twitter_count"].apply(convertInt)

        pd.concat([timestamp_series, total_mention_series, community_mention_series, insta_mention_series, blog_mention_series, news_mention_series, twitter_mention_series], axis=1)


        # 만든 df로부터 반환해야하는 형식에 맞게 자료형 생성.
        total_mention_list = pd.concat([timestamp_series, total_mention_series], axis=1).values.tolist()
        community_mention_list = pd.concat([timestamp_series, community_mention_series], axis=1).values.tolist()
        insta_mention_list = pd.concat([timestamp_series, insta_mention_series], axis=1).values.tolist()
        blog_mention_list = pd.concat([timestamp_series, blog_mention_series], axis=1).values.tolist()
        news_mention_list = pd.concat([timestamp_series, news_mention_series], axis=1).values.tolist()
        twitter_mention_list = pd.concat([timestamp_series, twitter_mention_series], axis=1).values.tolist()

        total_mention[keyword_key] = total_mention_list
        community_mention[keyword_key] = community_mention_list
        insta_mention[keyword_key] = insta_mention_list
        blog_mention[keyword_key] = blog_mention_list
        news_mention[keyword_key] = news_mention_list
        twitter_mention[keyword_key] = twitter_mention_list



        # total_mention[keyword_key] = []
        # community_mention[keyword_key] = []
        # insta_mention[keyword_key] = []
        # blog_mention[keyword_key] = []
        # news_mention[keyword_key] = []
        # twitter_mention[keyword_key] = []
        #
        # # 데이터가 없다면 패스
        # if value.empty == True:
        #     total_mention_sum[keyword_key] = 0
        #     community_mention_sum[keyword_key] = 0
        #     insta_mention_sum[keyword_key] = 0
        #     blog_mention_sum[keyword_key] = 0
        #     news_mention_sum[keyword_key] = 0
        #     twitter_mention_sum[keyword_key] = 0
        #     continue
        #
        # total_mention_sum[keyword_key] = int(value["count_sum"].sum())
        # community_mention_sum[keyword_key] = int(value["community_count"].sum())
        # insta_mention_sum[keyword_key] = int(value["insta_count"].sum())
        # blog_mention_sum[keyword_key] = int(value["blog_count"].sum())
        # news_mention_sum[keyword_key] = int(value["news_count"].sum())
        # twitter_mention_sum[keyword_key] = int(value["twitter_count"].sum())
        #
        # # 하나의 키워드에 대해 기간 반복하여 데이터 정리.
        # target_date_datetime = datetime.date(start_date_datetime.year, start_date_datetime.month, start_date_datetime.day)
        # while target_date_datetime <= end_date_datetime:
        #     total_row = []
        #     community_row = []
        #     insta_row = []
        #     blog_row = []
        #     news_row = []
        #     twitter_row = []
        #
        #     total_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
        #     community_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
        #     insta_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
        #     blog_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
        #     news_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
        #     twitter_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
        #
        #     mention_count = value[value["term_start"] == target_date_datetime.isoformat()]
        #     if mention_count.empty == True:
        #         total_row.append("null")
        #         community_row.append("null")
        #         insta_row.append("null")
        #         blog_row.append("null")
        #         news_row.append("null")
        #         twitter_row.append("null")
        #     else:
        #         # row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0][mention_source_dict[mention_source]["column_name"]]))
        #         total_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["count_sum"]))
        #         community_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["community_count"]))
        #         insta_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["insta_count"]))
        #         blog_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["blog_count"]))
        #         news_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["news_count"]))
        #         twitter_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["twitter_count"]))
        #
        #         total_mention_sum = total_mention_sum
        #
        #     total_mention[keyword_key].append(total_row)
        #     community_mention[keyword_key].append(community_row)
        #     insta_mention[keyword_key].append(insta_row)
        #     blog_mention[keyword_key].append(blog_row)
        #     news_mention[keyword_key].append(news_row)
        #     twitter_mention[keyword_key].append(twitter_row)
        #
        #     target_date_datetime += datetime.timedelta(days=1)

    # # 전체 언급량 데이터 합 구하기
    # total_mention_sum = []
    # for i in range(len(day_list)):
    #     sum = 0
    #     for keyword_key, value in total_mention.items():
    #         if len(value) - 1 < i:
    #             continue
    #         temp_value = value[i][1]
    #         if temp_value != 'null':
    #             sum += temp_value
    #     row = []
    #     row.append(day_list[i])
    #     row.append(sum)
    #     total_mention_sum.append(row)

    # context["keyword_list"] = keyword_list
    # context["mention_data"] = {
    #     "total_mention": {"count_list": total_mention, "name": "전체 언급량 추이"},
    #     "community_mention": {"count_list": community_mention, "name": "커뮤니티 언급량 추이"},
    #     "insta_mention": {"count_list": insta_mention, "name": "인스타 언급량 추이"},
    #     "blog_mention": {"count_list": blog_mention, "name": "블로그 언급량 추이"},
    #     "news_mention": {"count_list": news_mention, "name": "뉴스 언급량 추이"},
    #     "twitter_mention": {"count_list": twitter_mention, "name": "트위터 언급량 추이"},
    # }
    # context["xaxis_day_list"] = xaxis_day_list

    result = {
        "keyword_list": brand_keyword_list,
        # "mention_data": {
        #     "count_list": total_mention,
        #     "name": mention_source_dict[mention_source]["ko_name"]+" 언급량 추이"
        # },
        "mention_data": {
            "total_mention": {"count_list": total_mention, "name": "전체 언급량 추이", "count_sum": total_mention_sum},
            "community_mention": {"count_list": community_mention, "name": "커뮤니티 언급량 추이", "count_sum": community_mention_sum},
            "insta_mention": {"count_list": insta_mention, "name": "인스타 언급량 추이", "count_sum": insta_mention_sum},
            "blog_mention": {"count_list": blog_mention, "name": "블로그 언급량 추이", "count_sum": blog_mention_sum},
            "news_mention": {"count_list": news_mention, "name": "뉴스 언급량 추이", "count_sum": news_mention_sum},
            "twitter_mention": {"count_list": twitter_mention, "name": "트위터 언급량 추이", "count_sum": twitter_mention_sum},
        },
        "xaxis_day_list": xaxis_day_list,
    }

    return JsonResponse(result);

def pos_neg_data(request):
    start_date_iso = "2021-01-01"
    end_date_iso = datetime.date.today().isoformat()
    lv1 = ""
    lv2 = ""
    keyword_group_code = ""

    # url 쿼리 스트링 가져오기.
    if (request.GET.get("lv1", None) != None) & (request.GET.get("lv2", None) != None):
        lv1 = request.GET.get("lv1")
        lv2 = request.GET.get("lv2")
    else:
        lv1 = "지향점"
        lv2 = "기술력"

    if (request.GET.get("startDate", None) != None) & (request.GET.get("endDate", None) != None):
        start_date_iso = request.GET.get("startDate")
        end_date_iso = request.GET.get("endDate")

    # if (request.GET.get("keywordGroup", None) != None):
    #     keyword_group_code = request.GET.get("keywordGroup")
    # else:
    #     return

    # social_keyword_group_id = SocialKeywordGroup.objects.filter(code=keyword_group_code).value().id
    # keyword_list = pd.DataFrame(list(SocialKeywords.objects.filter(keyword_group=social_keyword_group_id, is_deleted=False, is_followed=True).values()))

    # lv에 해당하는 키워드 목록 가져오기.
    keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=brand_keyword_list, is_deleted=False, is_followed=True).values()))
    keyword_list = pd.DataFrame()
    for idx in keyword_df.index:
        keyword_row = keyword_df.loc[idx]

        # include_keyword_set = {}
        # if include_keyword_set_list[lv1][lv2]["and_or"] == "and":
        #     include_keyword_set = set(keyword_row["and_include_keyword_list"].split("\\"))
        # elif include_keyword_set_list[lv1][lv2]["and_or"] == "or":
        #     include_keyword_set = set(keyword_row["or_include_keyword_list"].split("\\"))
        include_keyword_set = set(keyword_row["or_include_keyword_list"].split("\\"))
        # if include_keyword_set == include_keyword_set_list[lv1][lv2]["include_list"]:
        if include_keyword_set == include_keyword_set_list[lv1][lv2]:
            keyword_list = keyword_list.append(keyword_row)
        # include_keyword_list = keyword_row["and_include_keyword_list"].split("\\")
        # if (include_keyword in include_keyword_list) & ("아파트" in include_keyword_list) & (len(include_keyword_list) == 2):
        #     keyword_list = keyword_list.append(keyword_row)

    # keyword_list = keyword_group[lv1][lv2]  # 해당하는 키워드 목록
    # keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=keyword_list, is_deleted=False, is_followed=True).values()))

    start_date_datetime = datetime.date(int(start_date_iso.split("-")[0]), int(start_date_iso.split("-")[1]), int(start_date_iso.split("-")[2]), )
    end_date_datetime = datetime.date(int(end_date_iso.split("-")[0]), int(end_date_iso.split("-")[1]), int(end_date_iso.split("-")[2]), )
    target_date_datetime = datetime.date(start_date_datetime.year, start_date_datetime.month, start_date_datetime.day)

    # 기간에 대한 전체 date리스트.
    day_list = []
    while target_date_datetime <= end_date_datetime:
        day_list.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
        target_date_datetime += datetime.timedelta(days=1)

    # 그래프 상에 x축에서 보여줄 date리스트.
    xaxis_day_list = []
    xaxis_term = int((end_date_datetime - start_date_datetime).days / 10)
    count = 0
    target_date_datetime = datetime.date(start_date_datetime.year, start_date_datetime.month, start_date_datetime.day)
    while target_date_datetime <= end_date_datetime:
        if count == xaxis_term:
            xaxis_day_list.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
            count = 0
        count += 1
        target_date_datetime += datetime.timedelta(days=1)


    # 긍, 부정어 데이터 처리
    df = pd.DataFrame(list(ServicePosNegWords.objects.filter(
        keyword_id__in=keyword_list["id"], term_start__gt=start_date_iso, term_end__lt=end_date_iso,
        term_type="W"
    ).order_by("-word_count").values("term_start", "term_end", "word", "word_count", "rank", "pos_neg", "property", "keyword_id")))

    pos_neg_data = {}
    # if df.empty == False:
    for keyword_idx in keyword_list.index:
        keyword_id = keyword_list["id"][keyword_idx]
        keyword = keyword_list["keyword"][keyword_idx]

        pos_neg_data[keyword] = {
            "table": [],
            "wordCloud": [],
            "graph": {"pos": [], "neg": [], "neu": []},
            "count_sum": {"pos": 0, "neg": 0, "neu":0}
        }

        if df.empty:
            continue

        temp_df = df[df["keyword_id"] == keyword_id]
        if temp_df.empty == True:
            continue

        a = temp_df.groupby(["word", "pos_neg", "property"], as_index=False).sum("word_count").sort_values(by="word_count", ascending=False)

        table_data = []
        wordCloud_data = []
        graph_data = {
            "pos": [],
            "neg": [],
            "neu": [],
        }

        pos_count_sum = int(a[a["pos_neg"]=="POS"]["word_count"].sum())
        neg_count_sum = int(a[a["pos_neg"]=="NEG"]["word_count"].sum())
        neu_count_sum = int(a[a["pos_neg"]=="NEU"]["word_count"].sum())
        count_sum = {
            "pos": pos_count_sum,
            "neg": neg_count_sum,
            "neu": neu_count_sum,
        }

        # 테이블 데이터, 워드클라우드 데이터 처리.
        # biggest_value = a.iloc[0]["word_count"]
        # div_value = 1
        # while (biggest_value/1000) == 0:
        #     div_value = div_value*10
        #     biggest_value = int(biggest_value/div_value)

        for row in a.values:
            table_data.append(row.tolist())
            wordCloud_data.append([row[0], row[3], row[1], row[3]])

        # 그래프 데이터 처리.
        term_list_by_posneg_df = temp_df.groupby(["term_start", "term_end", "pos_neg"], as_index=False).sum("word_count").sort_values(by="term_start")
        term_list_df = temp_df.groupby(["term_start", "term_end"], as_index=False).sum("word_count").sort_values(by="term_start")
        term_list_temp = temp_df.groupby(["term_start"], as_index=False).sum("word_count").sort_values(by="term_start")
        term_list = []
        for term in term_list_temp["term_start"].values.tolist():
            term_datetime = datetime.date(int(term.split("-")[0]), int(term.split("-")[1]), int(term.split("-")[2]))
            term_list.append(calendar.timegm(term_datetime.timetuple()) * 1000)
        graph_data["term_list"] = term_list

        # 수정본
        def convertIsoToTimestamp(iso):
            iso_datetime = common_util.iso_to_datetime(iso)
            return calendar.timegm(iso_datetime.timetuple()) * 1000
        timestamp_list = term_list_df["term_start"].apply(convertIsoToTimestamp)

        pos_neg_data_df = temp_df.groupby(["term_start", "term_end", "pos_neg"], ).sum("word_count").unstack(fill_value=0)
        def convertInt(x):
            return int(x)
        if "POS" in pos_neg_data_df["word_count"].columns :
           pos_series = pos_neg_data_df["word_count"]["POS"].apply(convertInt)
           pos_series.index = range(pos_series.size)
           pos_list = pd.concat([timestamp_list, pos_series], axis=1).values.tolist()
           graph_data["pos"] = pos_list
        if "NEG" in pos_neg_data_df["word_count"].columns :
           neg_series = pos_neg_data_df["word_count"]["NEG"].apply(convertInt)
           neg_series.index = range(neg_series.size)
           neg_list = pd.concat([timestamp_list, neg_series], axis=1).values.tolist()
           graph_data["neg"] = neg_list
        if "NEU" in pos_neg_data_df["word_count"].columns :
           neu_series = pos_neg_data_df["word_count"]["NEU"].apply(convertInt)
           neu_series.index = range(neu_series.size)
           neu_list = pd.concat([timestamp_list, neu_series], axis=1).values.tolist()
           graph_data["neu"] = neu_list

        # neg_series = pos_neg_data_df["word_count"]["NEG"].apply(convertInt)
        # neu_series = pos_neg_data_df["word_count"]["NEU"].apply(convertInt)
        #
        # pos_series.index = range(pos_series.size)
        # neg_series.index = range(neg_series.size)
        # neu_series.index = range(neu_series.size)
        #
        # pos_list = pd.concat([timestamp_list, pos_series], axis=1).values.tolist()
        # neg_list = pd.concat([timestamp_list, neg_series], axis=1).values.tolist()
        # neu_list = pd.concat([timestamp_list, neu_series], axis=1).values.tolist()
        #
        # graph_data["pos"] = pos_list
        # graph_data["neg"] = neg_list
        # graph_data["neu"] = neu_list


        # for term_list_df_idx in term_list_df.index:
        #     term_start = term_list_df["term_start"][term_list_df_idx]
        #     term_end = term_list_df["term_end"][term_list_df_idx]
        #     # pos_neg = term_list_df["pos_neg"][term_list_df_idx]
        #     # count = int(term_list_df["word_count"][term_list_df_idx])
        #
        #     term_start_datetime = datetime.date(int(term_start.split("-")[0]), int(term_start.split("-")[1]), int(term_start.split("-")[2]))
        #
        #     target_term_posneg_sum = term_list_by_posneg_df[term_list_by_posneg_df["term_start"] == term_start]
        #     pos_sum_df = target_term_posneg_sum[target_term_posneg_sum["pos_neg"] == "POS"]
        #     neg_sum_df = target_term_posneg_sum[target_term_posneg_sum["pos_neg"] == "NEG"]
        #     neu_sum_df = target_term_posneg_sum[target_term_posneg_sum["pos_neg"] == "NEU"]
        #
        #     pos_sum = 0
        #     neg_sum = 0
        #     neu_sum = 0
        #
        #     if pos_sum_df.empty == False:
        #         pos_sum = int(pos_sum_df.iloc[0]["word_count"])
        #     if neg_sum_df.empty == False:
        #         neg_sum = int(neg_sum_df.iloc[0]["word_count"])
        #     if neu_sum_df.empty == False:
        #         neu_sum = int(neu_sum_df.iloc[0]["word_count"])
        #
        #     graph_data["pos"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, pos_sum])
        #     graph_data["neg"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, neg_sum])
        #     graph_data["neu"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, neu_sum])
        #
        #     # if pos_neg == "POS":
        #     #     graph_data["pos"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])
        #     # elif pos_neg == "NEG":
        #     #     graph_data["neg"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])
        #     # elif pos_neg == "NEU":
        #     #     graph_data["neu"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])

        pos_neg_data[keyword] = {
            "table": table_data,
            "wordCloud": wordCloud_data[:30],
            "graph": graph_data,
            "count_sum": count_sum,
        }

    result = pos_neg_data

    return JsonResponse(result)

class PeopleIframe(LoginRequiredMixin, TemplateView):
    name=""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stock_list_df = pd.DataFrame(list(BasicInfo.objects.exclude(corp_code=' ').values()))

        for stock_idx in stock_list_df.index:
            stock_df = stock_list_df.loc[stock_idx]
            stock_code = stock_df["code"]

            print("stock_code : "+stock_code)

            def aaa(lv, original_df, account_list_df, parent_account_id, subject_name):
                result = {}
                lv_0_list = account_list_df[account_list_df["account_level"] == lv]  # 항목 리스트 중 lv 0 리스트.
                for index, lv_0 in lv_0_list.iterrows():
                    account_id = lv_0["account_id"]

                    # 항목들 parent_account_id 업데이트.
                    # row_list = FinancialStatement.objects.filter(code=stock_code, subject_name="현금흐름표", account_id=lv_0["account_id"]).all()
                    # for row in row_list:
                    #     row.parent_account_id = parent_account_id
                    #     row.save(update_fields=["parent_account_id"])

                    db = psycopg2.connect(host="112.220.72.179", dbname="openmetric", user="openmetric",
                                          password=")!metricAdmin01", port=2345)
                    cur = db.cursor()
                    cur.execute(
                        "update stock_financial_statement set parent_account_id='" + parent_account_id + "' where code_id='" + stock_code + "' and subject_name='" + subject_name + "' and account_id='" +
                        lv_0["account_id"] + "'")
                    db.commit()

                    # row_list.update(parent_account_id=parent_account_id)
                    # row.parent_account_id = account_id
                    # row.save()

                    lv_0_account_name = lv_0["account_name"].split("_")[lv]

                    # 해당 항목의 하위 항목들 추출.
                    lv_0_low_list = pd.DataFrame(columns=account_list_df.columns)
                    for index, r in account_list_df.iterrows():
                        if (lv_0_account_name == r["account_name"].split("_")[lv]) & (r["account_level"] > lv):
                            lv_0_low_list = pd.DataFrame.append(lv_0_low_list, r)
                    if len(lv_0_low_list) <= 0:
                        continue
                    # lv_1_list = lv_0_low_list[lv_0_low_list["account_level"] == (lv+1)]

                    result.update(aaa(lv + 1, original_df, lv_0_low_list, account_id, subject_name))

                return result

            # parent_account_id 할당이 이미 되었는지 확인.
            temp_query_set = FinancialStatement.objects.filter(code_id=stock_code, subject_name="현금흐름표", parent_account_id__isnull=True)
            if temp_query_set.count() != 0:
                cashflow_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code_id=stock_code, subject_name="현금흐름표").values()))
                # cashflow_statement = cashflow_statement.dropna()
                cashflow_statement_account = cashflow_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

                aaa(0, cashflow_statement, cashflow_statement_account, "", "현금흐름표")

            temp_query_set = FinancialStatement.objects.filter(code_id=stock_code, subject_name="포괄손익계산서", parent_account_id__isnull=True)
            if temp_query_set.count() != 0:
                income_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code_id=stock_code, subject_name="포괄손익계산서").values()))
                # cashflow_statement = cashflow_statement.dropna()
                income_statement_account = income_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

                aaa(0, income_statement, income_statement_account, "", "포괄손익계산서")

            temp_query_set = FinancialStatement.objects.filter(code_id=stock_code, subject_name="재무상태표", parent_account_id__isnull=True)
            if temp_query_set.count() != 0:
                balance_sheet = pd.DataFrame(list(FinancialStatement.objects.filter(code_id=stock_code, subject_name="재무상태표").values()))
                # cashflow_statement = cashflow_statement.dropna()
                balance_sheet_account = balance_sheet.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

                aaa(0, balance_sheet, balance_sheet_account, "", "재무상태표")

            pass

        pass

class PricePredict(LoginRequiredMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        basic_info_list = BasicInfo.objects.exclude(corp_code=" ").order_by("code").all()
        for basic_info in basic_info_list:
            stock_code = basic_info.code
            term = "week"

            print("stock_code : "+stock_code)

            for i in reversed(range(1, 6)):
                today = datetime.datetime.today()
                today = datetime.datetime(2021, 8, 31)
                this_week_monthday = today - datetime.timedelta(days=today.weekday())
                target_week = this_week_monthday - datetime.timedelta(days=7*i)

                target_week_iso = common_util.datetime_to_iso(target_week)

                k = target_week_iso

                print("target_week : "+k)

                pp = StockPricePredictService(stock_code, "week")
                pp.save_predict_data(k)

                basicInfo = BasicInfo.objects.filter(code=stock_code).get()
                # newObj = StockPricePredict(code=basicInfo, date=k,
                #                   account_code="S", account_name="시가", account_value=pp.S(k))
                # newObj.save()


                # print("S : "+str(pp.S(k)))
                # print("H : " + str(pp.H(k)))
                # print("L : "+str(pp.L(k)))
                # print("E : " + str(pp.E(k)))
                # print("G : " + str(pp.G(k)))
                # print("Gp : " + str(pp.Gp(k)))
                # print("HLk : " + str(pp.HLk(k)))
                # print("HLk3d : " + str(pp.HLk3d(k)))
                # print("HLk5d : " + str(pp.HLk5d(k)))
                # print("HLk10d : " + str(pp.HLk10d(k)))
                # print("HLk20d : " + str(pp.HLk20d(k)))
                # print("HLpk : " + str(pp.HLpk(k)))
                # print("HLpk3d : " + str(pp.HLpk3d(k)))
                # print("HLpk5d : " + str(pp.HLpk5d(k)))
                # print("HLpk10 : " + str(pp.HLpk10(k)))
                # print("HLpk20 : " + str(pp.HLpk20(k)))
                # print("HSk : " + str(pp.HSk(k)))
                # print("HSk3d : " + str(pp.HSk_n_d(k, 3)))
                # print("HSk5d : " + str(pp.HSk_n_d(k, 5)))
                # print("HSk10d : " + str(pp.HSk_n_d(k, 10)))
                # print("HSk20d : " + str(pp.HSk_n_d(k, 20)))
                #
                # print("SLk : " + str(pp.SLk(k)))
                # print("SLk3d : " + str(pp.SLk_n_d(k, 3)))
                # print("SLk5d : " + str(pp.SLk_n_d(k, 5)))
                # print("SLk10d : " + str(pp.SLk_n_d(k, 10)))
                # print("SLk20d : " + str(pp.SLk_n_d(k, 20)))
                #
                # print("3EHP1 : " + str(pp.n_EHP1(k, 3)))
                # print("3ELP1 : " + str(pp.n_ELP1(k, 3)))
                # print("5EHP1 : " + str(pp.n_EHP1(k, 5)))
                # print("5ELP1 : " + str(pp.n_ELP1(k, 5)))
                # print("10EHP1 : " + str(pp.n_EHP1(k, 10)))
                # print("10ELP1 : " + str(pp.n_ELP1(k, 10)))
                # print("20EHP1 : " + str(pp.n_EHP1(k, 20)))
                # print("20ELP1 : " + str(pp.n_ELP1(k, 20)))
                #
                # print("3HLW1 : " + str(pp.n_HLW1(k, 3)))
                # print("5HLW1 : " + str(pp.n_HLW1(k, 5)))
                # print("10HLW1 : " + str(pp.n_HLW1(k, 10)))
                # print("20HLW1 : " + str(pp.n_HLW1(k, 20)))
                #
                # print("3HLMA1 : " + str(pp.n_HLMA1(k, 3)))
                # print("5HLMA1 : " + str(pp.n_HLMA1(k, 5)))
                # print("10HLMA1 : " + str(pp.n_HLMA1(k, 10)))
                # print("20HLMA1 : " + str(pp.n_HLMA1(k, 20)))
                #
                # print("3HPEE1 : " + str(pp.n_HPEE1(k, 3)))
                # print("3LPEE1 : " + str(pp.n_LPEE1(k, 3)))
                # print("5HPEE1 : " + str(pp.n_HPEE1(k, 5)))
                # print("5LPEE1 : " + str(pp.n_LPEE1(k, 5)))
                # print("10HPEE1 : " + str(pp.n_HPEE1(k, 10)))
                # print("10LPEE1 : " + str(pp.n_LPEE1(k, 10)))
                # print("20HPEE1 : " + str(pp.n_HPEE1(k, 20)))
                # print("20LPEE1 : " + str(pp.n_LPEE1(k, 20)))
                #
                # print("3HPEEA1 : " + str(pp._3HPEEA1(k)))
                # print("3LPEEA1 : " + str(pp._3LPEEA1(k)))
                # # 2차
                # print("3EHP2 : " + str(pp.n_EHP2(k, 3)))
                # print("3ELP2 : " + str(pp.n_ELP2(k, 3)))
                # print("5EHP2 : " + str(pp.n_EHP2(k, 5)))
                # print("5ELP2 : " + str(pp.n_ELP2(k, 5)))
                # print("10EHP2 : " + str(pp.n_EHP2(k, 10)))
                # print("10ELP2 : " + str(pp.n_ELP2(k, 10)))
                # print("20EHP2 : " + str(pp.n_EHP2(k, 20)))
                # print("20ELP2 : " + str(pp.n_ELP2(k, 20)))
                #
                # print("3HLW2 : " + str(pp.n_HLW2(k, 3)))
                # print("5HLW2 : " + str(pp.n_HLW2(k, 5)))
                # print("10HLW2 : " + str(pp.n_HLW2(k, 10)))
                # print("20HLW2 : " + str(pp.n_HLW2(k, 20)))
                #
                # print("3HLMA2 : " + str(pp.n_HLMA2(k, 3)))
                # print("5HLMA2 : " + str(pp.n_HLMA2(k, 5)))
                # print("10HLMA2 : " + str(pp.n_HLMA2(k, 10)))
                # print("20HLMA2 : " + str(pp.n_HLMA2(k, 20)))
                #
                # print("3HPEE2 : " + str(pp.n_HPEE2(k, 3)))
                # print("3LPEE2 : " + str(pp.n_LPEE2(k, 3)))
                # print("5HPEE2 : " + str(pp.n_HPEE2(k, 5)))
                # print("5LPEE2 : " + str(pp.n_LPEE2(k, 5)))
                # print("10HPEE2 : " + str(pp.n_HPEE2(k, 10)))
                # print("10LPEE2 : " + str(pp.n_LPEE2(k, 10)))
                # print("20HPEE2 : " + str(pp.n_HPEE2(k, 20)))
                # print("20LPEE2 : " + str(pp.n_LPEE2(k, 20)))
                #
                # print("3HPEEA2 : " + str(pp._3HPEEA2(k)))
                # print("3LPEEA2 : " + str(pp._3LPEEA2(k)))
                #
                # print("3EHP3 : " + str(pp.n_EHP3(k, 3)))
                # print("3ELP3 : " + str(pp.n_ELP3(k, 3)))
                # print("5EHP3 : " + str(pp.n_EHP3(k, 5)))
                # print("5ELP3 : " + str(pp.n_ELP3(k, 5)))
                # print("10EHP3 : " + str(pp.n_EHP3(k, 10)))
                # print("10ELP3 : " + str(pp.n_ELP3(k, 10)))
                # print("20EHP3 : " + str(pp.n_EHP3(k, 20)))
                # print("20ELP3 : " + str(pp.n_ELP3(k, 20)))
                #
                # print("3HLW3 : " + str(pp.n_HLW3(k, 3)))
                # print("5HLW3 : " + str(pp.n_HLW3(k, 5)))
                # print("10HLW3 : " + str(pp.n_HLW3(k, 10)))
                # print("20HLW3 : " + str(pp.n_HLW3(k, 20)))
                #
                # print("3HLMA3 : " + str(pp.n_HLMA3(k, 3)))
                # print("5HLMA3 : " + str(pp.n_HLMA3(k, 5)))
                # print("10HLMA3 : " + str(pp.n_HLMA3(k, 10)))
                # print("20HLMA3 : " + str(pp.n_HLMA3(k, 20)))
                #
                # print("3HPEE3 : " + str(pp.n_HPEE3(k, 3)))
                # print("3LPEE3 : " + str(pp.n_LPEE3(k, 3)))
                # print("5HPEE3 : " + str(pp.n_HPEE3(k, 5)))
                # print("5LPEE3 : " + str(pp.n_LPEE3(k, 5)))
                # print("10HPEE3 : " + str(pp.n_HPEE3(k, 10)))
                # print("10LPEE3 : " + str(pp.n_LPEE3(k, 10)))
                # print("20HPEE3 : " + str(pp.n_HPEE3(k, 20)))
                # print("20LPEE3 : " + str(pp.n_LPEE3(k, 20)))
                #
                # print("3HPEEA3 : " + str(pp._3HPEEA3(k)))
                # print("3LPEEA3 : " + str(pp._3LPEEA3(k)))
                #
                # print("3EHP123 : " + str(pp.n_EHP123(k, 3)))
                # print("3ELP123 : " + str(pp.n_ELP123(k, 3)))
                # print("5EHP123 : " + str(pp.n_EHP123(k, 5)))
                # print("5ELP123 : " + str(pp.n_ELP123(k, 5)))
                # print("10EHP123 : " + str(pp.n_EHP123(k, 10)))
                # print("10ELP123 : " + str(pp.n_ELP123(k, 10)))
                # print("20EHP123 : " + str(pp.n_EHP123(k, 20)))
                # print("20ELP123 : " + str(pp.n_ELP123(k, 20)))
                #
                # print("3HLW123 : " + str(pp.n_HLW123(k, 3)))
                # print("5HLW123 : " + str(pp.n_HLW123(k, 5)))
                # print("10HLW123 : " + str(pp.n_HLW123(k, 10)))
                # print("20HLW123 : " + str(pp.n_HLW123(k, 20)))
                #
                # print("3HLMA123 : " + str(pp.n_HLMA123(k, 3)))
                # print("5HLMA123 : " + str(pp.n_HLMA123(k, 5)))
                # print("10HLMA123 : " + str(pp.n_HLMA123(k, 10)))
                # print("20HLMA123 : " + str(pp.n_HLMA123(k, 20)))
                #
                # print("3HPEE123 : " + str(pp.n_HPEE123(k, 3)))
                # print("3LPEE123 : " + str(pp.n_LPEE123(k, 3)))
                # print("5HPEE123 : " + str(pp.n_HPEE123(k, 5)))
                # print("5LPEE123 : " + str(pp.n_LPEE123(k, 5)))
                # print("10HPEE123 : " + str(pp.n_HPEE123(k, 10)))
                # print("10LPEE123 : " + str(pp.n_LPEE123(k, 10)))
                # print("20HPEE123 : " + str(pp.n_HPEE123(k, 20)))
                # print("20LPEE123 : " + str(pp.n_LPEE123(k, 20)))
                #
                # print("3HPEEA123 : " + str(pp._3HPEEA123(k)))
                # print("3LPEEA123 : " + str(pp._3LPEEA123(k)))
                #
                # print("3EHP23 : " + str(pp.n_EHP23(k, 3)))
                # print("3ELP23 : " + str(pp.n_ELP23(k, 3)))
                # print("5EHP23 : " + str(pp.n_EHP23(k, 5)))
                # print("5ELP23 : " + str(pp.n_ELP23(k, 5)))
                # print("10EHP23 : " + str(pp.n_EHP23(k, 10)))
                # print("10ELP23 : " + str(pp.n_ELP23(k, 10)))
                # print("20EHP23 : " + str(pp.n_EHP23(k, 20)))
                # print("20ELP23 : " + str(pp.n_ELP23(k, 20)))
                #
                # # 12차
                # print("3HLW23 : " + str(pp.n_HLW23(k, 3)))
                # print("5HLW23 : " + str(pp.n_HLW23(k, 5)))
                # print("10HLW23 : " + str(pp.n_HLW23(k, 10)))
                # print("20HLW23 : " + str(pp.n_HLW23(k, 20)))
                #
                # print("3HLMA23 : " + str(pp.n_HLMA23(k, 3)))
                # print("5HLMA23 : " + str(pp.n_HLMA23(k, 5)))
                # print("10HLMA23 : " + str(pp.n_HLMA23(k, 10)))
                # print("20HLMA23 : " + str(pp.n_HLMA23(k, 20)))
                #
                # print("3HPEE23 : " + str(pp.n_HPEE23(k, 3)))
                # print("3LPEE23 : " + str(pp.n_LPEE23(k, 3)))
                # print("5HPEE23 : " + str(pp.n_HPEE23(k, 5)))
                # print("5LPEE23 : " + str(pp.n_LPEE23(k, 5)))
                # print("10HPEE23 : " + str(pp.n_HPEE23(k, 10)))
                # print("10LPEE23 : " + str(pp.n_LPEE23(k, 10)))
                # print("20HPEE23 : " + str(pp.n_HPEE23(k, 20)))
                # print("20LPEE23 : " + str(pp.n_LPEE23(k, 20)))
                #
                # print("3HPEEA23 : " + str(pp._3HPEEA23(k)))
                # print("3LPEEA23 : " + str(pp._3LPEEA23(k)))
                #
                # print("3EHP12 : " + str(pp.n_EHP12(k, 3)))
                # print("3ELP12 : " + str(pp.n_ELP12(k, 3)))
                # print("5EHP12 : " + str(pp.n_EHP12(k, 5)))
                # print("5ELP12 : " + str(pp.n_ELP12(k, 5)))
                # print("10EHP12 : " + str(pp.n_EHP12(k, 10)))
                # print("10ELP12 : " + str(pp.n_ELP12(k, 10)))
                # print("20EHP12 : " + str(pp.n_EHP12(k, 20)))
                # print("20ELP12 : " + str(pp.n_ELP12(k, 20)))
                #
                # print("3HLW12 : " + str(pp.n_HLW12(k, 3)))
                # print("5HLW12 : " + str(pp.n_HLW12(k, 5)))
                # print("10HLW12 : " + str(pp.n_HLW12(k, 10)))
                # print("20HLW12 : " + str(pp.n_HLW12(k, 20)))
                #
                # print("3HLMA12 : " + str(pp.n_HLMA12(k, 3)))
                # print("5HLMA12 : " + str(pp.n_HLMA12(k, 5)))
                # print("10HLMA12 : " + str(pp.n_HLMA12(k, 10)))
                # print("20HLMA12 : " + str(pp.n_HLMA12(k, 20)))
                #
                # print("3HPEE12 : " + str(pp.n_HPEE12(k, 3)))
                # print("3LPEE12 : " + str(pp.n_LPEE12(k, 3)))
                # print("5HPEE12 : " + str(pp.n_HPEE12(k, 5)))
                # print("5LPEE12 : " + str(pp.n_LPEE12(k, 5)))
                # print("10HPEE12 : " + str(pp.n_HPEE12(k, 10)))
                # print("10LPEE12 : " + str(pp.n_LPEE12(k, 10)))
                # print("20HPEE12 : " + str(pp.n_HPEE12(k, 20)))
                # print("20LPEE12 : " + str(pp.n_LPEE12(k, 20)))
                #
                # print("3HPEEA12 : " + str(pp._3HPEEA12(k)))
                # print("3LPEEA12 : " + str(pp._3LPEEA12(k)))
                # print(" : " + str(pp.))



        return context

class NewsAnalysis(LoginRequiredMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 언론사 리스트 추가.
        press_list = news_reactions.objects.order_by("press").all().values("press").annotate(Count("press"))
        press_list = [x["press"] for x in press_list]

        context["press_list"] = press_list

        return context

# 채시보 - 기사 리스트 검색
def search_news_list(request):
    result = {}

    press = request.GET.get("press")
    start_date = request.GET.get("startDate")
    end_date = request.GET.get("endDate")
    search_keyword = request.GET.get("searchKeyword")
    exclude_keyword = request.GET.get("excludeKeyword")
    source_site = request.GET.get("sourceSite")

    # 컬럼 생성.
    if source_site == "naver_news":
        result["column_list"] = ["id", "종목명", "종목 코드", "제목", "링크", "언론사", "소스 사이트", "날짜", "반응수", "댓글수", "좋아요", "훈훈해요", "슬퍼요", "화나요", "후속기사 원해요"]
    elif source_site == "daum_news":
        result["column_list"] = ["id", "종목명", "종목 코드", "제목", "링크", "언론사", "소스 사이트", "날짜", "반응수", "댓글수", "좋아요", "훈훈해요", "슬퍼요", "화나요", "추천해요"]

    # 리스트 생성.
    if press == "all":
        news_list = news_reactions.objects.filter(
            date__gte=start_date, date__lte=end_date, source=source_site, title__contains=search_keyword
        ).order_by("-date").values()
    else:
        news_list = news_reactions.objects.filter(
            press=press, date__gte=start_date, date__lte=end_date, source=source_site, title__contains=search_keyword
        ).order_by("-date").values()

    if exclude_keyword != "":
        news_list = news_list.exclude(title__contains=exclude_keyword)

    news_list = pd.DataFrame(list(news_list))

    if news_list.empty == False:
        news_list.drop(axis="columns", labels=["created_at", "updated_at"], inplace=True)
        news_list["code_id"] = news_list["code_id"].str.replace("A", "")

        if source_site == "naver_news":
            news_list.drop(axis="columns", labels=["emotion_recommend_cnt"], inplace=True)
        elif source_site == "daum_news":
            news_list.drop(axis="columns", labels=["emotion_want_cnt"], inplace=True)

        result["news_list"] = news_list.values.tolist()
    else:
        result["news_list"] = []

    return JsonResponse(result)



# auth pages
custom_pages_coming_soon_view = CustomView.as_view(template_name="extra/coming-soon.html")
custom_pages_faqs_view = CustomView.as_view(template_name="extra/faqs.html")
custom_pages_gallery_view = CustomView.as_view(template_name="extra/gallery.html")
custom_pages_invoice_view = CustomView.as_view(template_name="extra/invoice.html")
custom_pages_maintenance_view = CustomView.as_view(template_name="extra/maintenance.html")
custom_pages_pricing_view = CustomView.as_view(template_name="extra/pricing.html")
custom_pages_search_results_view = CustomView.as_view(template_name="extra/search-results.html")
custom_pages_sitemap_view = CustomView.as_view(template_name="extra/sitemap.html")
custom_pages_starter_view = CustomView.as_view(template_name="extra/starter.html")
custom_pages_timeline_view = CustomView.as_view(template_name="extra/timeline.html")
custom_pages_404_alt_view = CustomView.as_view(template_name="extra/404-alt.html")
custom_pages_404_two_view = CustomView.as_view(template_name="extra/404-two.html")
custom_pages_404_view = CustomView.as_view(template_name="extra/404.html")
custom_pages_500_two_view = CustomView.as_view(template_name="extra/500-two.html")
custom_pages_500_view = CustomView.as_view(template_name="extra/500.html")

price_analysis_view = PriceAnalysisView.as_view(template_name='pages/price-analysis.html')
social_analysis_view = SocialAnalysisView.as_view(template_name='pages/social-analysis.html')
people_iframe = PeopleIframe.as_view(template_name="pages/peopleIframe.html")

price_predict_view = PricePredict.as_view(template_name="pages/peopleIframe.html")

news_analysis_view = NewsAnalysis.as_view(template_name="pages/news-analysis.html")
