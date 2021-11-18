import calendar

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.db.models import Count

from ubold.pages import common_util
from ubold.stocks.models import StaffNumber, BoardMemberAverageWage, BoardMemberPersonalWage, SocialKeywords, ServiceMentionCounts, \
    ServicePosNegWords
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


class CompanyInfoView(LoginRequiredMixin, TemplateView):
    stock_code = ""
    search_keyword = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result_list = []

        # 테스트
        # df = pd.DataFrame(list(FinancialStatement.objects.filter(code="A000040", subject_name="재무상태표")
        #                        .order_by("created_at").values()))
        # df = df.dropna()
        # balance_sheet_account = balance_sheet.groupby(["account_id", "account_level", "account_name"], as_index=False).all()  # 항목 리스트.
        # df_account = df.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

        # code 인자 확인
        if "code" in kwargs:
            self.stock_code = kwargs["code"]
        # 검색어 확인
        if self.request.GET.get("searchKeyword", None) != None:
            self.search_keyword = self.request.GET.get("searchKeyword")

        # 검색어로 종목 검색 및 주요 지표 계산.
        if (self.search_keyword != "") :
            today = datetime.date.today()
            today_date = today
            if today.weekday() > 4:  # 오늘이 토,일요일이라면
                today = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=4)
                today_date = today
                today = today.isoformat()

            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            yesterday_date = yesterday
            if yesterday.weekday() > 4:
                yesterday = yesterday - datetime.timedelta(days=yesterday.weekday()) + datetime.timedelta(days=4)
                yesterday_date = yesterday
                yesterday = yesterday.isoformat()
            today = "2021-09-13"
            today_date = datetime.date(2021,9,13)
            yesterday = "2021-09-10"
            yesterday_date = datetime.date(2021,9,10)

            # 페이징 확인
            if "stock_info_page" in kwargs:
                stock_info_page = kwargs["stock_info_page"]
            else:
                stock_info_page = 1

            db = psycopg2.connect(host="112.220.72.179", dbname="openmetric", user="openmetric",
                                  password=")!metricAdmin01", port=2345)
            cur = db.cursor()
            stock_list = pd.read_sql("select * from stocks_basic_info where corp_code!=' ' "
                                     "and name like '%"+self.search_keyword+"%' "
                                     "order by code "
                                     "offset "+str(stock_info_page-1)+\
                                     " ", db)
            fin_list = pd.read_sql("select "
                                   "  code_id, this_term_name, subject_name, account_id, this_term_amount "
                                   "from stock_financial_statement fs "
                                   "where "
                                   "    code_id in('"+("\',\'").join(stock_list["code"].tolist())+"') "
                                   "  and ((subject_name='재무상태표' and (account_id='8111' or account_id='8900')) "
                                   "  or (subject_name='포괄손익계산서' and (account_id='1100' or account_id='8200'))) "
                                   "  and this_term_name = (select max(this_term_name) from stock_financial_statement fs2 where fs2.code_id = fs.code_id) "
                                   # "  and code_id='A000020'  "
                                   "", db) \
                .sort_values(by="code_id")
            price_list = pd.read_sql("select * "
                                     "from stocks_historic_data hd "
                                     "where "
                                     "  code_id in('"+("\',\'").join(stock_list["code"].tolist())+"') "
                                     "  and (hd.date='" + today + "' or hd.date='" + yesterday + "') "
                                        # "  and code_id='A000020'"
                                        "  ", db).sort_values(by="code_id")

            for index, stock in stock_list.iterrows():
                code = stock["code"]
                # 발행 주식수
                stock_count = fin_list.loc[(fin_list["subject_name"] == "재무상태표") & (fin_list["account_id"] == "8111") & (fin_list["code_id"] == code)]
                if (stock_count.empty == True) or (np.isnan(stock_count.iloc[0]["this_term_amount"])):
                    stock_count = None
                else:
                    stock_count = stock_count.iloc[0]["this_term_amount"]
                # 오늘 주가
                today_price = price_list.loc[(price_list["code_id"] == code) & (price_list["date"] == today_date)]
                if (today_price.empty == True) or (np.isnan(today_price.iloc[0]["close_price"])):
                    today_price = None
                else:
                    today_price = today_price.iloc[0]["close_price"]
                # 어제 주가
                yesterday_price = price_list.loc[(price_list["code_id"] == code) & (price_list["date"] == yesterday_date)]
                if (yesterday_price.empty == True) or (np.isnan(yesterday_price.iloc[0]["close_price"])):
                    yesterday_price = None
                else:
                    yesterday_price = yesterday_price.iloc[0]["close_price"]
                # 거래량
                trade_volume = price_list.loc[(price_list["code_id"] == code) & (price_list["date"] == today_date)]
                if (trade_volume.empty == True) or (np.isnan(trade_volume.iloc[0]["transaction_volume"])):
                    trade_volume = None
                else:
                    trade_volume = trade_volume.iloc[0]["transaction_volume"]
                # 매출액
                profit = fin_list.loc[(fin_list["code_id"] == code) & (fin_list["subject_name"] == "포괄손익계산서") & (fin_list["account_id"] == "1100")]
                if (profit.empty == True) or (np.isnan(profit.iloc[0]["this_term_amount"])):
                    profit = None
                else:
                    profit = profit.iloc[0]["this_term_amount"]
                # 당기순이익
                net_income = fin_list.loc[(fin_list["code_id"] == code) & (fin_list["subject_name"] == "포괄손익계산서") & (fin_list["account_id"] == "8200")]
                if (net_income.empty == True) or (np.isnan(net_income.iloc[0]["this_term_amount"])):
                    net_income = None
                else:
                    net_income = net_income.iloc[0]["this_term_amount"]
                # 순자산
                total_capital = fin_list.loc[(fin_list["subject_name"] == "재무상태표") & (fin_list["account_id"] == "8900") & (fin_list["code_id"] == code)]
                if (total_capital.empty == True) or (np.isnan(total_capital.iloc[0]["this_term_amount"])):
                    total_capital = None
                else:
                    total_capital = total_capital.iloc[0]["this_term_amount"]

                if (stock_count == None) or (today_price == None):
                    market_cap = None
                else:
                    market_cap = format(int(stock_count * today_price), ",d")  # 시가총액

                if (stock_count == None) or (today_price == None) or (profit == None):
                    psr = None
                else:
                    psr = round(stock_count * today_price / profit, 2)

                if (stock_count == None) or (today_price == None) or (net_income == None):
                    per = None
                else:
                    per = round(today_price / (net_income / stock_count), 2)

                if (net_income == None) or (stock_count == None):
                    eps = None
                else:
                    eps = round(net_income / stock_count, 2)

                if (per == None) or (eps == None):
                    peg = None
                else:
                    peg = round(per / eps, 2)

                if (total_capital == None) or (stock_count == None):
                    bps = None
                else:
                    bps = round(total_capital / stock_count, 2)

                if (bps == None) or (today_price == None):
                    pbr = None
                else:
                    pbr = round(today_price / bps, 2)

                if (net_income == None) or (total_capital == None):
                    roe = None
                else:
                    roe = round(net_income / total_capital, 2)

                if (today_price == None) or (yesterday_price == None):
                    price_rate = None
                else:
                    price_rate = round(today_price / yesterday_price, 2)

                if today_price != None:
                    today_price = format(int(today_price), ",d")
                if trade_volume != None:
                    trade_volume = format(int(trade_volume), ",d")
                row = [stock["name"], market_cap, today_price, price_rate, trade_volume, psr, per, peg, pbr, eps, roe, code]
                result_list.append(row)

            context["stock_data_list"] = result_list

        #
        # 종목 리스트
        stock_list = BasicInfo.objects.exclude(corp_code=' ')

        # 종목 클릭시 데이터 로드.
        if self.stock_code != "":
            pass
            # # 주가 데이터 가져오기.
            # trade_data_list = HistoricData.objects.filter(code=self.stock_code).order_by("date")
            # close_price_list = list(trade_data_list.values_list("close_price", flat=True))
            # close_price_list = [int(x) for x in close_price_list]
            # trade_volume_list = list(trade_data_list.values_list("transaction_volume", flat=True))
            # data_date = list(trade_data_list.values_list("date", flat=True))
            # data_date = [x.isoformat() for x in data_date]
            #
            # context["close_price_list"] = close_price_list
            # context["trade_volume_list"] = trade_volume_list
            # context["data_date"] = data_date
            #
            # # 재무 데이터 그래프 데이터
            # financial_graph_data = {}
            # financial_graph_data1 = FinancialStatement.objects.filter(code=self.stock_code, subject_name="포괄손익계산서", account_name="수익")\
            #     .order_by("this_term_name")  # 수익 데이터.
            # financial_graph_data2 = FinancialStatement.objects.filter(code=self.stock_code, subject_name="포괄손익계산서", account_name="영업이익(손실)") \
            #     .order_by("this_term_name")  # 영업이익(손실) 데이터.
            # financial_graph_data3 = FinancialStatement.objects.filter(code=self.stock_code, subject_name="포괄손익계산서", account_name="총당기순이익") \
            #     .order_by("this_term_name")  # 총당기순이익 데이터.
            #
            # timestamp_list = []
            # temp_list = []
            # for x in list(financial_graph_data1):
            #     this_term_name = x.this_term_name.split("-")
            #     temp_datetime = datetime.datetime(int(this_term_name[0]), int(this_term_name[1]), int(this_term_name[2]))-datetime.timedelta(days=15)
            #     temp_list.append([calendar.timegm(temp_datetime.timetuple()) * 1000, int(x.this_term_amount)])
            #     timestamp_list.append(calendar.timegm(temp_datetime.timetuple())*1000)
            #     # temp_list.append([temp_datetime.isoformat()[:10], int(x.this_term_amount)])
            # financial_graph_data["financial_graph_data1"] = temp_list
            # financial_graph_data["timestamp_data"] = timestamp_list
            #
            # temp_list = []
            # for x in list(financial_graph_data2):
            #     this_term_name = x.this_term_name.split("-")
            #     temp_datetime = datetime.datetime(int(this_term_name[0]), int(this_term_name[1]), int(this_term_name[2]))-datetime.timedelta(days=15)
            #     temp_list.append([calendar.timegm(temp_datetime.timetuple()) * 1000, int(x.this_term_amount)])
            #     # temp_list.append([temp_datetime.isoformat()[:10], int(x.this_term_amount)])
            # financial_graph_data["financial_graph_data2"] = temp_list
            #
            # temp_list = []
            # for x in list(financial_graph_data3):
            #     this_term_name = x.this_term_name.split("-")
            #     temp_datetime = datetime.datetime(int(this_term_name[0]), int(this_term_name[1]), int(this_term_name[2]))-datetime.timedelta(days=15)
            #     temp_list.append([calendar.timegm(temp_datetime.timetuple()) * 1000, int(x.this_term_amount)])
            #     # temp_list.append([temp_datetime.isoformat()[:10], int(x.this_term_amount)])
            # financial_graph_data["financial_graph_data3"] = temp_list
            #
            # context["financial_graph_data"] = financial_graph_data

            # # 포괄손익계산서
            # income_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code=self.stock_code, subject_name="포괄손익계산서").values()))
            # income_statement = income_statement.dropna()
            # income_statement_account = income_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)
            #
            # term_list = FinancialStatement.objects.filter(code=self.stock_code).order_by("this_term_name") \
            #     .values("this_term_name").annotate(Count("this_term_name"))
            # term_list = [x["this_term_name"] for x in term_list]
            #
            # # 재무데이터 데이터들을 항목 순서와 하위 항목에 맞게 가공하는 메소드.
            # def aaa(lv, original_df, part_df, term_list, ):
            #     result = {}
            #     lv_0_list = part_df[part_df["account_level"] == lv]  # 항목 리스트 중 lv 0 리스트.
            #     for index, lv_0 in lv_0_list.iterrows():
            #         # 해당 항목 row 추가
            #         row = {}
            #         row["level"] = list(range(lv))
            #         row["data_list"] = {}
            #         for term in term_list:
            #             value = original_df[(original_df["this_term_name"] == term) & (original_df["account_id"] == lv_0["account_id"])]
            #             if value.empty == True:
            #                 row["data_list"][term] = ""
            #             else:
            #                 row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
            #         lv_0_account_name = lv_0["account_name"].split("_")[lv]
            #         result[lv_0_account_name] = row
            #         # 해당 항목의 하위 항목들 추출.
            #         lv_0_low_list = pd.DataFrame(columns=part_df.columns)
            #         for index, r in part_df.iterrows():
            #             if (lv_0_account_name == r["account_name"].split("_")[lv]) & (r["account_level"] > lv):
            #                 lv_0_low_list = pd.DataFrame.append(lv_0_low_list, r)
            #         if len(lv_0_low_list) <= 0:
            #             continue
            #         # lv_1_list = lv_0_low_list[lv_0_low_list["account_level"] == (lv+1)]
            #
            #         result.update(aaa(lv + 1, original_df, lv_0_low_list, term_list))
            #
            #     return result
            #
            # income_statement_list = aaa(0, income_statement, income_statement_account, term_list)
            #
            # context["income_statement"] = income_statement_list
            # context["income_statement_term_list"] = term_list
            #
            # # 재무상태표
            # balance_sheet = pd.DataFrame(list(FinancialStatement.objects.filter(code=self.stock_code, subject_name="재무상태표").values()))
            # balance_sheet = balance_sheet.dropna()
            # # balance_sheet_account = balance_sheet.groupby(["account_id", "account_level", "account_name"], as_index=False).all()  # 항목 리스트.
            # balance_sheet_account = balance_sheet.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)
            #
            # term_list = FinancialStatement.objects.filter(code=self.stock_code).order_by("this_term_name") \
            #     .values("this_term_name").annotate(Count("this_term_name"))
            # term_list = [x["this_term_name"] for x in term_list]
            #
            # # 테스트(테이블에서 순서 정보를 가지고 있는 경우)
            # balance_sheet = pd.DataFrame(list(FinancialStatement.objects.filter(code=self.stock_code, subject_name="재무상태표")
            #                                   .order_by("created_at").values()))
            # balance_sheet = balance_sheet.dropna()
            # balance_sheet_account = balance_sheet.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)
            # result = {}
            # for i in range(len(balance_sheet_account)):
            #     temp_row = balance_sheet_account.iloc[i]
            #
            #     row = {}
            #     row["level"] = list(range(temp_row["account_level"]))
            #     row["data_list"] = {}
            #     for term in term_list:
            #         value = balance_sheet[(balance_sheet["this_term_name"] == term) & (balance_sheet["account_id"] == temp_row["account_id"])]
            #         if value.empty == True:
            #             row["data_list"][term] = ""
            #         else:
            #             row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
            #     temp_account_name = temp_row["account_name"].split("_")[temp_row["account_level"]]
            #     result[temp_account_name] = row
            #
            # balance_sheet_list = aaa(0, balance_sheet, balance_sheet_account, term_list)
            #
            # context["balance_sheet"] = balance_sheet_list
            # context["balance_sheet_term_list"] = term_list
            #
            # # 현금흐름표
            # cashflow_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code=self.stock_code, subject_name="현금흐름표").values()))
            # cashflow_statement = cashflow_statement.dropna()
            # cashflow_statement_account = cashflow_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)
            #
            # term_list = FinancialStatement.objects.filter(code=self.stock_code).order_by("this_term_name") \
            #     .values("this_term_name").annotate(Count("this_term_name"))
            # term_list = [x["this_term_name"] for x in term_list]
            #
            # cashflow_statement_list = aaa(0, cashflow_statement, cashflow_statement_account, term_list)
            #
            # context["cashflow_statement"] = cashflow_statement_list
            # context["cashflow_statement_term_list"] = term_list
            #
            # # 증권사 컨센서스
            # Consensus.objects.filter(code_id=self.stock_code)
            #
            # # 공시
            # if "notice_year" in kwargs:
            #     notice_year = kwargs["notice_year"]
            # else:
            #     notice_year = str(datetime.date.today().year)
            # notice_list = DartSearchData.objects.filter(
            #     stock_code=self.stock_code, #data_date__gt=notice_year + "-01-01", data_date__lt=notice_year + "-12-31"
            # ).order_by("-data_date")
            #
            # context["notice_list"] = notice_list
            # #
            # # 주주정보
            # shareholder_list_data = {}
            # term_list = []
            # shareholder_graph_data = {}
            # shareholder_graph_timestamp_list = []
            # shareholder_list_df = pd.DataFrame(list(Shareholder.objects.filter(code_id=self.stock_code).values()))
            # shareholder_list_df = shareholder_list_df.dropna()
            # shareholder_name_list = shareholder_list_df.groupby(["shareholder_name"], as_index=False).all()
            #
            # term_list = Shareholder.objects.filter(code=self.stock_code).order_by("term_name") \
            #     .values("term_name").annotate(Count("term_name"))
            # term_list = [x["term_name"] for x in term_list]
            #
            #
            # for term_name in term_list:
            #     temp_term = term_name.split("-")
            #     temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            #     shareholder_graph_timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            #
            # for shareholder_name in shareholder_name_list["shareholder_name"]:
            #     shareholder_list_df[shareholder_list_df["shareholder_name"] == shareholder_name]
            #     row = {}
            #     graph_one_shareholder_row = []
            #     for term in term_list:
            #         graph_one_term = []
            #
            #         temp_term = term.split("-")
            #         temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            #         # graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            #         value = shareholder_list_df[(shareholder_list_df["term_name"] == term) & (shareholder_list_df["shareholder_name"] == shareholder_name)]
            #         if value.empty == True:
            #             row[term] = ""
            #             graph_one_term.append("")
            #         else:
            #             row[term] = value.iloc[0]["share_per"]
            #             graph_one_term.append(float(value.iloc[0]["share_per"]))
            #
            #         graph_one_shareholder_row.append(graph_one_term)
            #         graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            #     shareholder_graph_data[shareholder_name] = (graph_one_shareholder_row)
            #
            #     shareholder_list_data[shareholder_name] = row
            #
            # context["shareholder_list"] = shareholder_list_data
            # context["shareholder_term_list"] = term_list
            # context["shareholder_graph_data"] = shareholder_graph_data
            # context["shareholder_graph_timestamp_list"] = shareholder_graph_timestamp_list
            #
            # # 배당 정보
            # dividend_list_data = {}
            # term_list = []
            # dividend_graph_data = {}
            # dividend_graph_timestamp_list = []
            #
            # dividend_list_df = pd.DataFrame(list(Dividend.objects.filter(code_id=self.stock_code).values()))
            # dividend_list_df = dividend_list_df.dropna()
            # dividend_name_list = dividend_list_df.groupby(["account_name"], as_index=False).all()
            #
            # term_list = Dividend.objects.filter(code=self.stock_code).order_by("term_name") \
            #     .values("term_name").annotate(Count("term_name"))
            # term_list = [x["term_name"] for x in term_list]
            #
            # for term_name in term_list:
            #     temp_term = term_name.split("-")
            #     temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            #     dividend_graph_timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            # for account_name in dividend_name_list["account_name"]:
            #     dividend_list_df[dividend_list_df["account_name"] == account_name]
            #     row = {}
            #     graph_one_dividend_row = []
            #     for term in term_list:
            #         graph_one_term = []
            #
            #         temp_term = term.split("-")
            #         temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            #         graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            #         value = dividend_list_df[(dividend_list_df["term_name"] == term) & (dividend_list_df["account_name"] == account_name)]
            #         if value.empty == True:
            #             row[term] = ""
            #             graph_one_term.append("")
            #         else:
            #             row[term] = value.iloc[0]["value"]
            #             graph_one_term.append(float(value.iloc[0]["value"]))
            #
            #         graph_one_dividend_row.append(graph_one_term)
            #         # graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            #     dividend_list_data[account_name] = row
            #     dividend_graph_data[account_name] = graph_one_dividend_row
            #
            # context["dividend_list"] = dividend_list_data
            # context["dividend_term_list"] = term_list
            # context["dividend_graph_data"] = dividend_graph_data
            # context["dividend_graph_timestamp_list"] = dividend_graph_timestamp_list
            #
            # # 평균급여 및 종업원수
            # wcp_data = {}
            # wcp_item_name_list = []
            # wcp_term_list = []
            # wcp_df = pd.DataFrame(list(WorkerCountAndPay.objects.filter(code_id=self.stock_code).values()))
            # wcp_df = wcp_df.dropna()
            #
            # # if "worker_count_pay_term" in kwargs:
            # #     wcp_term = kwargs["worker_count_pay_term"]
            # # else:
            # #     wcp_term = wcp_df.max()["term_name"]
            # # wcp_df = wcp_df[wcp_df["term_name"] == wcp_term] #특정 기간에 대한 데이터만 남김.
            #
            # wcp_term_list = list(wcp_df.groupby(["term_name"], as_index=False).all()["term_name"])
            # for term_name in wcp_term_list:
            #     wcp_one_term_df = wcp_df[wcp_df["term_name"]==term_name]
            #     wcp_one_term_data = {}
            #
            #     wcp_category_list = wcp_one_term_df.groupby(["worker_category", "worker_sex"], as_index=False).all()
            #
            #     wcp_item_name_list = wcp_one_term_df.groupby(["item_name"], as_index=False).all()["item_name"]
            #     # item_name = WorkerCountAndPay.objects.filter(code=self.stock_code).order_by("item_name") \
            #     #     .values("term_name").annotate(Count("term_name"))
            #     # term_list = [x["term_name"] for x in term_list]
            #
            #     for index, wcp_category in wcp_category_list.iterrows():
            #         # for wcp_sex in wcp_category_list["worker_sex"]:
            #         row = {}
            #         for item_name in wcp_item_name_list:
            #             value = wcp_one_term_df[(wcp_one_term_df["item_name"] == item_name) &
            #                            (wcp_one_term_df["worker_category"] == wcp_category["worker_category"]) &
            #                            (wcp_one_term_df["worker_sex"] == wcp_category["worker_sex"])
            #                            ]
            #             if value.empty == True:
            #                 row[item_name] = ""
            #             else:
            #                 row[item_name] = str(value.iloc[0]["value"])
            #         worker_sex = ""
            #         if wcp_category["worker_sex"]=="m": worker_sex = "남"
            #         else: worker_sex="여"
            #         wcp_one_term_data[wcp_category["worker_category"]+"("+worker_sex+")"] = row
            #
            #     wcp_data[term_name] = wcp_one_term_data
            #
            # context["wcp_list"] = wcp_data
            # context["temp_wcp_data"] = wcp_data[wcp_term_list[len(wcp_term_list)-1]]
            # context["wcp_item_list"] = list(wcp_item_name_list)
            # context["wcp_term_list"] = wcp_term_list
            #
            # # 임직원 숫자 추이
            # staff_number = {}
            # term_list = []
            # staff_number_graph_data = {}
            # staff_number_graph_timestamp_list = []
            #
            # staff_number_list_df = pd.DataFrame(list(StaffNumber.objects.filter(code_id=self.stock_code).values()))
            # staff_number_list_df = staff_number_list_df.dropna()
            # staff_number_name_list = staff_number_list_df.groupby(["staff_type"], as_index=False).all()
            #
            # term_list = StaffNumber.objects.filter(code=self.stock_code).order_by("term_name") \
            #     .values("term_name").annotate(Count("term_name"))
            # term_list = [x["term_name"] for x in term_list]
            #
            # for term_name in term_list:
            #     if term_name.find("12-31") != -1:
            #         temp_term = term_name.split("-")
            #         temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            #         staff_number_graph_timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            # for staff_type in staff_number_name_list["staff_type"]:
            #     staff_number_list_df[staff_number_list_df["staff_type"] == staff_type]
            #     row = {}
            #     graph_one_staff_number_row = []
            #     for term in term_list:
            #         graph_one_term = []
            #
            #         temp_term = term.split("-")
            #         temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            #         graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            #         value = staff_number_list_df[(staff_number_list_df["term_name"] == term) & (staff_number_list_df["staff_type"] == staff_type)]
            #         if value.empty == True:
            #             row[term] = ""
            #             graph_one_term.append("")
            #         else:
            #             row[term] = value.iloc[0]["number"]
            #             graph_one_term.append(int(value.iloc[0]["number"]))
            #
            #         graph_one_staff_number_row.append(graph_one_term)
            #         # graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            #     # staff_number_list_data[staff_type] = row
            #     staff_number_graph_data[staff_type] = graph_one_staff_number_row
            #
            # # context["dividend_list"] = staff_number_list_data
            # # context["staff_number_term_list"] = term_list
            # context["staff_number_graph_data"] = staff_number_graph_data
            # context["staff_number_graph_timestamp_list"] = staff_number_graph_timestamp_list
            #
            # # 이사회 임원 평균 보수
            # staff_number = {}
            # term_list = []
            # bm_average_wage_graph_data = {}
            # bm_average_wage_graph_timestamp_list = []
            #
            # bm_average_wage_list_df = pd.DataFrame(list(BoardMemberAverageWage.objects.filter(code_id=self.stock_code).values()))
            # bm_average_wage_list_df = bm_average_wage_list_df.dropna()
            # # bm_average_wage_name_list = bm_average_wage_list_df.groupby(["staff_type"], as_index=False).all()
            #
            # term_list = BoardMemberAverageWage.objects.filter(code=self.stock_code).order_by("term_name") \
            #     .values("term_name").annotate(Count("term_name"))
            # term_list = [x["term_name"] for x in term_list]
            #
            # for term_name in term_list:
            #     if term_name.find("12-31") != -1:
            #         temp_term = term_name.split("-")
            #         temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            #         bm_average_wage_graph_timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            # total_wage_list = []
            # average_wage_list = []
            #
            # for df_idx in bm_average_wage_list_df.index:
            #     total_wage_row = []
            #     average_wage_row = []
            #     graph_one_bm_average_wage_row = []
            #
            #     term = bm_average_wage_list_df["term_name"][df_idx]
            #     total_wage = bm_average_wage_list_df["total_wage"][df_idx]
            #     average_wage = bm_average_wage_list_df["average_wage"][df_idx]
            #
            #     temp_term = term.split("-")
            #     temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            #     total_wage_row.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #     average_wage_row.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
            #
            #     value = bm_average_wage_list_df[(bm_average_wage_list_df["term_name"] == term)]
            #     if value.empty == True:
            #         total_wage_row.append("")
            #         average_wage_row.append("")
            #     else:
            #         total_wage_row.append(int(value.iloc[0]["total_wage"]))
            #         average_wage_row.append(int(value.iloc[0]["average_wage"]))
            #
            #     total_wage_list.append(total_wage_row)
            #     average_wage_list.append(average_wage_row)
            #
            # bm_average_wage_graph_data["total_wage"] = total_wage_list
            # bm_average_wage_graph_data["average_wage"] = average_wage_list
            #
            # # context["dividend_list"] = bm_average_wage_list_data
            # # context["bm_average_wage_term_list"] = term_list
            # context["bm_average_wage_graph_data"] = bm_average_wage_graph_data
            # context["bm_average_wage_graph_timestamp_list"] = bm_average_wage_graph_timestamp_list
            #
            #
            # # # 임원목록
            # # executives_data = {}
            # # executives_df = pd.DataFrame(list(Executives.objects.filter(code_id=self.stock_code).values()))
            # # executives_df = executives_df.dropna()
            # #
            # # if "executives_year" in kwargs:
            # #     executives_term = kwargs["executives_year"]
            # # else:
            # #     executives_term = executives_df.max()["term_name"]
            # # executives_df = executives_df[executives_df["term_name"] == executives_term]  # 특정 기간에 대한 데이터만 남김.
            #
            # # 이사회 임원 목록
            # board_member_df = pd.DataFrame(list(BoardMembers.objects.filter(code_id=self.stock_code).values()))
            # board_member_df = board_member_df.dropna()
            #
            # board_member_data = {}
            # board_member_data["list"] = {}
            # board_member_data["term_list"] = []
            #
            # board_member_term_list = list(board_member_df.groupby(["term_name"], as_index=False).all()["term_name"])
            # for term_name in board_member_term_list:
            #     board_member_one_term_df = board_member_df[board_member_df["term_name"]==term_name]
            #     board_member_one_term_df = board_member_one_term_df.drop(columns=["id", "created_at","updated_at","code_id","corp_code","term_name"])
            #     row_list = []
            #     for df_idx in board_member_one_term_df.index:
            #         row_list.append(list(board_member_one_term_df.loc[df_idx]))
            #
            #     board_member_data["list"][term_name] = row_list
            #
            # board_member_data["item_list"] = ["이름", "업무", "생년월일", "성별", "상태", "임기 기간", "임기 종료"]
            # board_member_data["term_list"] = board_member_term_list
            # board_member_data["last_term_data"] = board_member_data["list"][board_member_term_list[-1]]
            # context["board_member_data"] = board_member_data
            #
            # # 이사회 임원 보수 정보
            # bm_personal_wage_df = pd.DataFrame(list(BoardMemberPersonalWage.objects.filter(code_id=self.stock_code).values()))
            # bm_personal_wage_df = bm_personal_wage_df.dropna()
            #
            # bm_personal_wage_data = {}
            # bm_personal_wage_data["list"] = {}
            # bm_personal_wage_data["term_list"] = []
            #
            # bm_personal_wage_term_list = list(bm_personal_wage_df.groupby(["term_name"], as_index=False).all()["term_name"])
            # for term_name in bm_personal_wage_term_list:
            #     bm_personal_wage_one_term_df = bm_personal_wage_df[bm_personal_wage_df["term_name"] == term_name]
            #     bm_personal_wage_one_term_df = bm_personal_wage_one_term_df.drop(columns=["id", "created_at", "updated_at", "code_id", "corp_code", "term_name"])
            #     row_list = []
            #     for df_idx in bm_personal_wage_one_term_df.index:
            #         row_list.append(list(bm_personal_wage_one_term_df.loc[df_idx]))
            #
            #     bm_personal_wage_data["list"][term_name] = row_list
            #
            # bm_personal_wage_data["item_list"] = ["이름", "직책", "보수", "공시",]
            # bm_personal_wage_data["term_list"] = bm_personal_wage_term_list
            # bm_personal_wage_data["last_term_data"] = bm_personal_wage_data["list"][bm_personal_wage_term_list[-1]]
            # context["bm_personal_wage_data"] = bm_personal_wage_data
            #
            # # # 임원 보수 정보
            # # executive_wage_data = []
            # # executive_wage_df = pd.DataFrame(list(ExecutiveWage.objects.filter(code=self.stock_code).values()))
            # #
            # # if "executive_wage_term" in kwargs:
            # #     executive_wage_term = kwargs["executive_wage_term"]
            # # else:
            # #     executive_wage_term = executive_wage_df.max()["term_name"]
            # # executive_wage_df = executive_wage_df[executive_wage_df["term_name"] == executive_wage_term]
            # #
            # # for index, executive_wage in executive_wage_df.iterrows():
            # #     executive_wage_data.append(executive_wage.to_dict())
            # #
            # # context["executive_wage_list"] = executive_wage_data


        return context

def company_info_price_data(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") !=None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    # today_iso = str(today_datetime.year)+"-"+str(today_datetime.month)+"-"+str(today_datetime.day)

    term_start_datetime = datetime.date(today_datetime.year-5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)
    # term_start_iso = str(term_start_datetime.year)+"-"+str(term_start_datetime.month)+"-"+str(term_start_datetime.day)

    # 주가 데이터 가져오기.
    trade_data_list = HistoricData.objects.filter(code=stock_code, date__gt=term_start_iso, date__lt=today_iso).order_by("date")
    close_price_list = list(trade_data_list.values_list("close_price", flat=True))
    close_price_list = [int(x) for x in close_price_list]
    trade_volume_list = list(trade_data_list.values_list("transaction_volume", flat=True))
    data_date = list(trade_data_list.values_list("date", flat=True))
    data_date = [x.isoformat() for x in data_date]

    result["close_price_list"] = close_price_list
    result["trade_volume_list"] = trade_volume_list
    result["data_date"] = data_date

    return JsonResponse(result)

def company_info_financial_graph_data(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)


    # 재무 데이터 그래프 데이터
    financial_graph_data = {}
    financial_graph_data1 = FinancialStatement.objects.filter(code=stock_code, subject_name="포괄손익계산서", account_name="수익", this_term_name__gt=term_start_iso, this_term_name__lt=today_iso) \
        .order_by("this_term_name")  # 수익 데이터.
    financial_graph_data2 = FinancialStatement.objects.filter(code=stock_code, subject_name="포괄손익계산서", account_name="영업이익(손실)", this_term_name__gt=term_start_iso, this_term_name__lt=today_iso) \
        .order_by("this_term_name")  # 영업이익(손실) 데이터.
    financial_graph_data3 = FinancialStatement.objects.filter(code=stock_code, subject_name="포괄손익계산서", account_name="총당기순이익", this_term_name__gt=term_start_iso, this_term_name__lt=today_iso) \
        .order_by("this_term_name")  # 총당기순이익 데이터.

    timestamp_list = []
    temp_list = []
    for x in list(financial_graph_data1):
        this_term_name = x.this_term_name.split("-")
        temp_datetime = datetime.datetime(int(this_term_name[0]), int(this_term_name[1]), int(this_term_name[2])) - datetime.timedelta(days=15)
        temp_list.append([calendar.timegm(temp_datetime.timetuple()) * 1000, int(x.this_term_amount)])
        timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
        # temp_list.append([temp_datetime.isoformat()[:10], int(x.this_term_amount)])
    financial_graph_data["financial_graph_data1"] = temp_list
    financial_graph_data["timestamp_data"] = timestamp_list

    temp_list = []
    for x in list(financial_graph_data2):
        this_term_name = x.this_term_name.split("-")
        temp_datetime = datetime.datetime(int(this_term_name[0]), int(this_term_name[1]), int(this_term_name[2])) - datetime.timedelta(days=15)
        temp_list.append([calendar.timegm(temp_datetime.timetuple()) * 1000, int(x.this_term_amount)])
        # temp_list.append([temp_datetime.isoformat()[:10], int(x.this_term_amount)])
    financial_graph_data["financial_graph_data2"] = temp_list

    temp_list = []
    for x in list(financial_graph_data3):
        this_term_name = x.this_term_name.split("-")
        temp_datetime = datetime.datetime(int(this_term_name[0]), int(this_term_name[1]), int(this_term_name[2])) - datetime.timedelta(days=15)
        temp_list.append([calendar.timegm(temp_datetime.timetuple()) * 1000, int(x.this_term_amount)])
        # temp_list.append([temp_datetime.isoformat()[:10], int(x.this_term_amount)])
    financial_graph_data["financial_graph_data3"] = temp_list

    result = financial_graph_data
    return JsonResponse(result)

def company_info_income_statement_table_data(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 포괄손익계산서
    income_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code=stock_code, subject_name="포괄손익계산서", this_term_name__gt=term_start_iso, this_term_name__lt=today_iso).values()))
    income_statement = income_statement.dropna(subset=["this_term_amount"])
    income_statement_account = income_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

    term_list = FinancialStatement.objects.filter(code=stock_code, this_term_name__gt=term_start_iso, this_term_name__lt=today_iso).order_by("this_term_name") \
        .values("this_term_name").annotate(Count("this_term_name"))
    term_list = [x["this_term_name"] for x in term_list]

    # 재무데이터 데이터들을 항목 순서와 하위 항목에 맞게 가공하는 메소드.
    def aaa(lv, original_df, part_df, term_list, ):
        result = {}
        lv_0_list = part_df[part_df["account_level"] == lv]  # 항목 리스트 중 lv 0 리스트.
        for index, lv_0 in lv_0_list.iterrows():
            # 해당 항목 row 추가
            row = {}
            row["level"] = list(range(lv))
            row["data_list"] = {}
            for term in term_list:
                value = original_df[(original_df["this_term_name"] == term) & (original_df["account_id"] == lv_0["account_id"])]
                if value.empty == True:
                    row["data_list"][term] = ""
                else:
                    row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
            lv_0_account_name = lv_0["account_name"].split("_")[lv]
            result[lv_0_account_name] = row
            # 해당 항목의 하위 항목들 추출.
            lv_0_low_list = pd.DataFrame(columns=part_df.columns)
            for index, r in part_df.iterrows():
                # temp_df = r[(r["account_name"].split("_")[lv] == lv_0_account_name) & (r["account_level"] > lv)]
                if (lv_0_account_name == r["account_name"].split("_")[lv]) & (r["account_level"] > lv):
                    lv_0_low_list = pd.DataFrame.append(lv_0_low_list, r)
            if len(lv_0_low_list) <= 0:
                continue
            # lv_1_list = lv_0_low_list[lv_0_low_list["account_level"] == (lv+1)]

            result.update(aaa(lv + 1, original_df, lv_0_low_list, term_list))

        return result

    def aaa2(lv, original_df, total_account_list, current_account_list, term_list, ):
        result = {}
        lv_0_list = current_account_list[current_account_list["account_level"] == lv]  # 항목 리스트 중 lv 0 리스트.
        for index, lv_0 in lv_0_list.iterrows():
            account_id = lv_0["account_id"]
            # 해당 항목 row 추가
            row = {}
            row["level"] = list(range(lv))
            row["data_list"] = {}
            for term in term_list:
                value = original_df[(original_df["this_term_name"] == term) & (original_df["account_id"] == lv_0["account_id"])]
                if value.empty == True:
                    row["data_list"][term] = ""
                else:
                    row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
            lv_0_account_name = lv_0["account_name"].split("_")[lv]
            result[lv_0_account_name] = row

            low_list = total_account_list[total_account_list["parent_account_id"] == account_id]

            result.update(aaa2(lv + 1, original_df, total_account_list, low_list, term_list))

        return result

    # # 테스트(테이블에서 순서 정보를 가지고 있는 경우)
    # cashflow_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code=stock_code, subject_name="포괄손익계산서")
    #                                   .order_by("created_at").values()))
    # cashflow_statement = cashflow_statement.dropna()
    # cashflow_statement_account = cashflow_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)
    # data_list = {}
    # for i in range(len(cashflow_statement_account)):
    #     temp_row = cashflow_statement_account.iloc[i]
    #
    #     row = {}
    #     row["level"] = list(range(temp_row["account_level"]))
    #     row["data_list"] = {}
    #     for term in term_list:
    #         value = cashflow_statement[(cashflow_statement["this_term_name"] == term) & (cashflow_statement["account_id"] == temp_row["account_id"])]
    #         if value.empty == True:
    #             row["data_list"][term] = ""
    #         else:
    #             row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
    #     temp_account_name = temp_row["account_name"].split("_")[temp_row["account_level"]]
    #     data_list[temp_account_name] = row

    income_statement_list = aaa2(0, income_statement, income_statement_account, income_statement_account, term_list)

    result["income_statement"] = income_statement_list
    result["income_statement_term_list"] = term_list

    return JsonResponse(result)

def company_info_balance_sheet_table_data(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 재무상태표
    balance_sheet = pd.DataFrame(list(FinancialStatement.objects.filter(code=stock_code, subject_name="재무상태표", this_term_name__gt=term_start_iso, this_term_name__lt=today_iso).order_by("account_id").values()))
    balance_sheet = balance_sheet.dropna(subset=["this_term_amount"])
    # balance_sheet_account = balance_sheet.groupby(["account_id", "account_level", "account_name"], as_index=False).all()  # 항목 리스트.
    balance_sheet_account = balance_sheet.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

    term_list = FinancialStatement.objects.filter(code=stock_code, this_term_name__gt=term_start_iso, this_term_name__lt=today_iso).order_by("this_term_name") \
        .values("this_term_name").annotate(Count("this_term_name"))
    term_list = [x["this_term_name"] for x in term_list]

    def aaa2(lv, original_df, total_account_list, current_account_list, term_list, ):
        result = {}
        lv_0_list = current_account_list[current_account_list["account_level"] == lv]  # 항목 리스트 중 lv 0 리스트.
        for index, lv_0 in lv_0_list.iterrows():
            account_id = lv_0["account_id"]
            # 해당 항목 row 추가
            row = {}
            row["level"] = list(range(lv))
            row["data_list"] = {}
            for term in term_list:
                value = original_df[(original_df["this_term_name"] == term) & (original_df["account_id"] == lv_0["account_id"])]
                if value.empty == True:
                    row["data_list"][term] = ""
                else:
                    row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
            lv_0_account_name = lv_0["account_name"].split("_")[lv]
            result[lv_0_account_name] = row

            low_list = total_account_list[total_account_list["parent_account_id"] == account_id]

            result.update(aaa2(lv + 1, original_df, total_account_list, low_list, term_list))

        return result

    def aaa(lv, original_df, part_df, term_list, ):
        result = {}
        lv_0_list = part_df[part_df["account_level"] == lv]  # 항목 리스트 중 lv 0 리스트.
        for index, lv_0 in lv_0_list.iterrows():
            # 해당 항목 row 추가
            row = {}
            row["level"] = list(range(lv))
            row["data_list"] = {}
            for term in term_list:
                value = original_df[(original_df["this_term_name"] == term) & (original_df["account_id"] == lv_0["account_id"])]
                if value.empty == True:
                    row["data_list"][term] = ""
                else:
                    row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
            lv_0_account_name = lv_0["account_name"].split("_")[lv]
            result[lv_0_account_name] = row
            # 해당 항목의 하위 항목들 추출.
            lv_0_low_list = pd.DataFrame(columns=part_df.columns)
            for index, r in part_df.iterrows():
                # temp_df = r[(r["account_name"].split("_")[lv] == lv_0_account_name) & (r["account_level"] > lv)]
                if (lv_0_account_name == r["account_name"].split("_")[lv]) & (r["account_level"] > lv):
                    lv_0_low_list = pd.DataFrame.append(lv_0_low_list, r)
            if len(lv_0_low_list) <= 0:
                continue
            # lv_1_list = lv_0_low_list[lv_0_low_list["account_level"] == (lv+1)]

            result.update(aaa(lv + 1, original_df, lv_0_low_list, term_list))

        return result

    balance_sheet_list = aaa2(0, balance_sheet, balance_sheet_account, balance_sheet_account, term_list)

    result["balance_sheet"] = balance_sheet_list
    result["balance_sheet_term_list"] = term_list

    return JsonResponse(result)

def company_info_cashflow_table_data(request):
    stock_code = "A000020"
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 현금흐름표
    cashflow_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code=stock_code, subject_name="현금흐름표", this_term_name__gt=term_start_iso, this_term_name__lt=today_iso).order_by("account_id").values()))
    cashflow_statement = cashflow_statement.dropna(subset=["this_term_amount"])
    cashflow_statement_account = cashflow_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

    term_list = FinancialStatement.objects.filter(code=stock_code, this_term_name__gt=term_start_iso, this_term_name__lt=today_iso).order_by("this_term_name") \
        .values("this_term_name").annotate(Count("this_term_name"))
    term_list = [x["this_term_name"] for x in term_list]

    def aaa(lv, original_df, total_account_list, current_account_list, term_list, ):
        result = {}
        lv_0_list = current_account_list[current_account_list["account_level"] == lv]  # 항목 리스트 중 lv 0 리스트.
        for index, lv_0 in lv_0_list.iterrows():
            account_id = lv_0["account_id"]
            # 해당 항목 row 추가
            row = {}
            row["level"] = list(range(lv))
            row["data_list"] = {}
            for term in term_list:
                value = original_df[(original_df["this_term_name"] == term) & (original_df["account_id"] == lv_0["account_id"])]
                if value.empty == True:
                    row["data_list"][term] = ""
                else:
                    row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
            lv_0_account_name = lv_0["account_name"].split("_")[lv]
            result[lv_0_account_name] = row

            low_list = total_account_list[total_account_list["parent_account_id"] == account_id]

            # # 해당 항목의 하위 항목들 추출.
            # lv_0_low_list = pd.DataFrame(columns=part_df.columns)
            # for index, r in part_df.iterrows():
            #     if (lv_0_account_name == r["account_name"].split("_")[lv]) & (r["account_level"] > lv):
            #         lv_0_low_list = pd.DataFrame.append(lv_0_low_list, r)
            # if len(lv_0_low_list) <= 0:
            #     continue
            # # lv_1_list = lv_0_low_list[lv_0_low_list["account_level"] == (lv+1)]

            result.update(aaa(lv + 1, original_df, total_account_list, low_list, term_list))

        return result

    # # 테스트(테이블에서 순서 정보를 가지고 있는 경우)
    # cashflow_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code=stock_code, subject_name="현금흐름표")
    #                                   .order_by("created_at").values()))
    # cashflow_statement = cashflow_statement.dropna()
    # cashflow_statement_account = cashflow_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)
    # data_list = {}
    # for i in range(len(cashflow_statement_account)):
    #     temp_row = cashflow_statement_account.iloc[i]
    #
    #     row = {}
    #     row["level"] = list(range(temp_row["account_level"]))
    #     row["data_list"] = {}
    #     for term in term_list:
    #         value = cashflow_statement[(cashflow_statement["this_term_name"] == term) & (cashflow_statement["account_id"] == temp_row["account_id"])]
    #         if value.empty == True:
    #             row["data_list"][term] = ""
    #         else:
    #             row["data_list"][term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
    #     temp_account_name = temp_row["account_name"].split("_")[temp_row["account_level"]]
    #     data_list[temp_account_name] = row

    cashflow_statement_list = aaa(0, cashflow_statement, cashflow_statement_account, cashflow_statement_account, term_list)

    result["cashflow_statement"] = cashflow_statement_list
    result["cashflow_statement_term_list"] = term_list

    return JsonResponse(result)

def company_info_notice(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    notice_list = pd.DataFrame(list(DartSearchData.objects.filter(
        stock_code=stock_code, #data_date__gt=notice_year + "-01-01", data_date__lt=notice_year + "-12-31"
    ).order_by("-data_date")))

    result = notice_list.values.tolist()

    return JsonResponse(result, safe=False)

def company_info_shareholder(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year-5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 주주정보
    shareholder_list_data = {}
    term_list = []
    shareholder_graph_data = {}
    shareholder_graph_timestamp_list = []
    shareholder_list_df = pd.DataFrame(list(Shareholder.objects.filter(code_id=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).values()))
    shareholder_list_df = shareholder_list_df.dropna()
    # last_term_name = shareholder_list_df.max(axis=0)["term_name"]
    shareholder_name_list = shareholder_list_df.groupby(["shareholder_name"], as_index=False).all()
    # sorted_shareholder_name_list = pd.DataFrame(list((Shareholder.objects.filter(code_id=stock_code, term_name=last_term_name).order_by("-share_per").values())))

    term_list = Shareholder.objects.filter(code=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).order_by("term_name") \
        .values("term_name").annotate(Count("term_name"))
    term_list = [x["term_name"] for x in term_list]

    for term_name in term_list:
        temp_term = term_name.split("-")
        temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
        shareholder_graph_timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

    for shareholder_name in shareholder_name_list["shareholder_name"]:
        shareholder_list_df[shareholder_list_df["shareholder_name"] == shareholder_name]
        row = {}
        graph_one_shareholder_row = []
        for term in term_list:
            graph_one_term = []

            temp_term = term.split("-")
            temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            # graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

            value = shareholder_list_df[(shareholder_list_df["term_name"] == term) & (shareholder_list_df["shareholder_name"] == shareholder_name)]
            if value.empty == True:
                row[term] = ""
                graph_one_term.append("")
            else:
                row[term] = value.iloc[0]["share_per"]
                graph_one_term.append(float(value.iloc[0]["share_per"]))

            graph_one_shareholder_row.append(graph_one_term)
            graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

        shareholder_graph_data[shareholder_name] = (graph_one_shareholder_row)

        shareholder_list_data[shareholder_name] = row

    result["shareholder_list"] = shareholder_list_data
    result["shareholder_term_list"] = term_list
    result["shareholder_graph_data"] = shareholder_graph_data
    result["shareholder_graph_timestamp_list"] = shareholder_graph_timestamp_list

    return JsonResponse(result)

def company_info_dividend(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 배당 정보
    dividend_list_data = {}
    term_list = []
    dividend_graph_data = {}
    dividend_graph_timestamp_list = []

    dividend_list_df = pd.DataFrame(list(Dividend.objects.filter(code_id=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).values()))
    dividend_list_df = dividend_list_df.dropna()
    dividend_name_list = dividend_list_df.groupby(["account_name"], as_index=False).all()

    term_list = Dividend.objects.filter(code=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).order_by("term_name") \
        .values("term_name").annotate(Count("term_name"))
    term_list = [x["term_name"] for x in term_list]

    for term_name in term_list:
        temp_term = term_name.split("-")
        temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
        dividend_graph_timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

    for account_name in dividend_name_list["account_name"]:
        dividend_list_df[dividend_list_df["account_name"] == account_name]
        row = {}
        graph_one_dividend_row = []
        for term in term_list:
            graph_one_term = []

            temp_term = term.split("-")
            temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

            value = dividend_list_df[(dividend_list_df["term_name"] == term) & (dividend_list_df["account_name"] == account_name)]
            if value.empty == True:
                row[term] = ""
                graph_one_term.append("")
            else:
                row[term] = value.iloc[0]["value"]
                graph_one_term.append(float(value.iloc[0]["value"]))

            graph_one_dividend_row.append(graph_one_term)
            # graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

        dividend_list_data[account_name] = row
        dividend_graph_data[account_name] = graph_one_dividend_row

    result["dividend_list"] = dividend_list_data
    result["dividend_term_list"] = term_list
    result["dividend_graph_data"] = dividend_graph_data
    result["dividend_graph_timestamp_list"] = dividend_graph_timestamp_list

    return JsonResponse(result)

def company_info_wcp(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 평균급여 및 종업원수
    wcp_data = {}
    wcp_item_name_list = []
    wcp_term_list = []
    wcp_df = pd.DataFrame(list(WorkerCountAndPay.objects.filter(code_id=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).values()))
    wcp_df = wcp_df.dropna()

    # if "worker_count_pay_term" in kwargs:
    #     wcp_term = kwargs["worker_count_pay_term"]
    # else:
    #     wcp_term = wcp_df.max()["term_name"]
    # wcp_df = wcp_df[wcp_df["term_name"] == wcp_term] #특정 기간에 대한 데이터만 남김.

    wcp_term_list = list(wcp_df.groupby(["term_name"], as_index=False).all()["term_name"])
    for term_name in wcp_term_list:
        wcp_one_term_df = wcp_df[wcp_df["term_name"]==term_name]
        wcp_one_term_data = {}

        wcp_category_list = wcp_one_term_df.groupby(["worker_category", "worker_sex"], as_index=False).all()

        wcp_item_name_list = wcp_one_term_df.groupby(["item_name"], as_index=False).all()["item_name"]
        # item_name = WorkerCountAndPay.objects.filter(code=self.stock_code).order_by("item_name") \
        #     .values("term_name").annotate(Count("term_name"))
        # term_list = [x["term_name"] for x in term_list]

        for index, wcp_category in wcp_category_list.iterrows():
            # for wcp_sex in wcp_category_list["worker_sex"]:
            row = {}
            for item_name in wcp_item_name_list:
                value = wcp_one_term_df[(wcp_one_term_df["item_name"] == item_name) &
                               (wcp_one_term_df["worker_category"] == wcp_category["worker_category"]) &
                               (wcp_one_term_df["worker_sex"] == wcp_category["worker_sex"])
                               ]
                if value.empty == True:
                    row[item_name] = ""
                else:
                    row[item_name] = str(value.iloc[0]["value"])
            worker_sex = ""
            if wcp_category["worker_sex"]=="m": worker_sex = "남"
            else: worker_sex="여"
            wcp_one_term_data[wcp_category["worker_category"]+"("+worker_sex+")"] = row

        wcp_data[term_name] = wcp_one_term_data

    result["wcp_list"] = wcp_data
    result["temp_wcp_data"] = wcp_data[wcp_term_list[len(wcp_term_list)-1]]
    result["wcp_item_list"] = list(wcp_item_name_list)
    result["wcp_term_list"] = wcp_term_list

    return JsonResponse(result)

def company_info_staff_number(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 임직원 숫자 추이
    staff_number = {}
    term_list = []
    staff_number_graph_data = {}
    staff_number_graph_timestamp_list = []

    staff_number_list_df = pd.DataFrame(list(StaffNumber.objects.filter(code_id=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).values()))
    staff_number_list_df = staff_number_list_df.dropna()
    staff_number_name_list = staff_number_list_df.groupby(["staff_type"], as_index=False).all()

    term_list = StaffNumber.objects.filter(code=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).order_by("term_name") \
        .values("term_name").annotate(Count("term_name"))
    term_list = [x["term_name"] for x in term_list]

    for term_name in term_list:
        if term_name.find("12-31") != -1:
            temp_term = term_name.split("-")
            temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            staff_number_graph_timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

    for staff_type in staff_number_name_list["staff_type"]:
        staff_number_list_df[staff_number_list_df["staff_type"] == staff_type]
        row = {}
        graph_one_staff_number_row = []
        for term in term_list:
            graph_one_term = []

            temp_term = term.split("-")
            temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

            value = staff_number_list_df[(staff_number_list_df["term_name"] == term) & (staff_number_list_df["staff_type"] == staff_type)]
            if value.empty == True:
                row[term] = ""
                graph_one_term.append("")
            else:
                row[term] = value.iloc[0]["number"]
                graph_one_term.append(int(value.iloc[0]["number"]))

            graph_one_staff_number_row.append(graph_one_term)
            # graph_one_term.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

        # staff_number_list_data[staff_type] = row
        staff_number_graph_data[staff_type] = graph_one_staff_number_row

    # context["dividend_list"] = staff_number_list_data
    # context["staff_number_term_list"] = term_list
    result["staff_number_graph_data"] = staff_number_graph_data
    result["staff_number_graph_timestamp_list"] = staff_number_graph_timestamp_list

    return JsonResponse(result)

def company_info_bm_average_wage(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 이사회 임원 평균 보수
    staff_number = {}
    term_list = []
    bm_average_wage_graph_data = {}
    bm_average_wage_graph_timestamp_list = []

    bm_average_wage_list_df = pd.DataFrame(list(BoardMemberAverageWage.objects.filter(code_id=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).values()))
    bm_average_wage_list_df = bm_average_wage_list_df.dropna()
    # bm_average_wage_name_list = bm_average_wage_list_df.groupby(["staff_type"], as_index=False).all()

    term_list = BoardMemberAverageWage.objects.filter(code=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).order_by("term_name") \
        .values("term_name").annotate(Count("term_name"))
    term_list = [x["term_name"] for x in term_list]

    for term_name in term_list:
        if term_name.find("12-31") != -1:
            temp_term = term_name.split("-")
            temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
            bm_average_wage_graph_timestamp_list.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

    total_wage_list = []
    average_wage_list = []

    for df_idx in bm_average_wage_list_df.index:
        total_wage_row = []
        average_wage_row = []
        graph_one_bm_average_wage_row = []

        term = bm_average_wage_list_df["term_name"][df_idx]
        total_wage = bm_average_wage_list_df["total_wage"][df_idx]
        average_wage = bm_average_wage_list_df["average_wage"][df_idx]

        temp_term = term.split("-")
        temp_datetime = datetime.datetime(int(temp_term[0]), int(temp_term[1]), int(temp_term[2]))
        total_wage_row.append(calendar.timegm(temp_datetime.timetuple()) * 1000)
        average_wage_row.append(calendar.timegm(temp_datetime.timetuple()) * 1000)

        value = bm_average_wage_list_df[(bm_average_wage_list_df["term_name"] == term)]
        if value.empty == True:
            total_wage_row.append("")
            average_wage_row.append("")
        else:
            total_wage_row.append(int(value.iloc[0]["total_wage"]))
            average_wage_row.append(int(value.iloc[0]["average_wage"]))

        total_wage_list.append(total_wage_row)
        average_wage_list.append(average_wage_row)

    bm_average_wage_graph_data["total_wage"] = total_wage_list
    bm_average_wage_graph_data["average_wage"] = average_wage_list

    # context["dividend_list"] = bm_average_wage_list_data
    # context["bm_average_wage_term_list"] = term_list
    result["bm_average_wage_graph_data"] = bm_average_wage_graph_data
    result["bm_average_wage_graph_timestamp_list"] = bm_average_wage_graph_timestamp_list

    return JsonResponse(result)

def company_info_board_member(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 이사회 임원 목록
    board_member_df = pd.DataFrame(list(BoardMembers.objects.filter(code_id=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).values()))
    board_member_df = board_member_df.dropna()

    board_member_data = {}
    board_member_data["list"] = {}
    board_member_data["term_list"] = []

    board_member_term_list = list(board_member_df.groupby(["term_name"], as_index=False).all()["term_name"])
    for term_name in board_member_term_list:
        board_member_one_term_df = board_member_df[board_member_df["term_name"]==term_name]
        board_member_one_term_df = board_member_one_term_df.drop(columns=["id", "created_at","updated_at","code_id","corp_code","term_name"])
        row_list = []
        for df_idx in board_member_one_term_df.index:
            row_list.append(list(board_member_one_term_df.loc[df_idx]))

        board_member_data["list"][term_name] = row_list

    board_member_data["item_list"] = ["이름", "업무", "생년월일", "성별", "상태", "임기 기간", "임기 종료"]
    board_member_data["term_list"] = board_member_term_list
    board_member_data["last_term_data"] = board_member_data["list"][board_member_term_list[-1]]
    result = board_member_data

    return JsonResponse(result)

def company_info_bm_personal_wage(request):
    stock_code = ""
    result = {}

    if request.GET.get("stock_code") != None:
        stock_code = request.GET.get("stock_code")
    else:
        return

    today_datetime = datetime.datetime.today()
    today_iso = common_util.datetime_to_iso(today_datetime)
    term_start_datetime = datetime.date(today_datetime.year - 5, today_datetime.month, today_datetime.day)
    term_start_iso = common_util.datetime_to_iso(term_start_datetime)

    # 이사회 임원 보수 정보
    bm_personal_wage_df = pd.DataFrame(list(BoardMemberPersonalWage.objects.filter(code_id=stock_code, term_name__gt=term_start_iso, term_name__lt=today_iso).values()))
    bm_personal_wage_df = bm_personal_wage_df.dropna()

    bm_personal_wage_data = {}
    bm_personal_wage_data["list"] = {}
    bm_personal_wage_data["term_list"] = []

    bm_personal_wage_term_list = list(bm_personal_wage_df.groupby(["term_name"], as_index=False).all()["term_name"])
    for term_name in bm_personal_wage_term_list:
        bm_personal_wage_one_term_df = bm_personal_wage_df[bm_personal_wage_df["term_name"] == term_name]
        bm_personal_wage_one_term_df = bm_personal_wage_one_term_df.drop(columns=["id", "created_at", "updated_at", "code_id", "corp_code", "term_name"])
        row_list = []
        for df_idx in bm_personal_wage_one_term_df.index:
            row_list.append(list(bm_personal_wage_one_term_df.loc[df_idx]))

        bm_personal_wage_data["list"][term_name] = row_list

    bm_personal_wage_data["item_list"] = ["이름", "직책", "보수", "공시",]
    bm_personal_wage_data["term_list"] = bm_personal_wage_term_list
    bm_personal_wage_data["last_term_data"] = bm_personal_wage_data["list"][bm_personal_wage_term_list[-1]]
    result = bm_personal_wage_data

    return JsonResponse(result)


# 메뉴 레벨에 해당하는 키워드 목록을 가져와, 그 키워드들에 대한 데이터들을 적절한 형태로 가공하여 페이지로 반환.
class SocialAnalysisView(LoginRequiredMixin, TemplateView):
    lv1 = ""
    lv2 = ""
    start_date = ""
    end_date = ""

    keyword = {
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if ("lv1" in kwargs) & ("lv2" in kwargs):
            lv1 = kwargs["lv1"]
            lv2 = kwargs["lv2"]
        else:
            return context

        # url 쿼리 스트링 가져오기.
        if (self.request.GET.get("startDate", None) != None) & (self.request.GET.get("endDate", None) != None):
            self.start_date = self.request.GET.get("startDate")
            self.end_date = self.request.GET.get("endDate")
        else:
            self.start_date = "2021-01-01"
            self.end_date = datetime.date.today().isoformat()

        # lv에 해당하는 키워드 목록 가져오기.
        keyword_list = self.keyword[lv1][lv2]# 해당하는 키워드 목록
        keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=keyword_list, is_deleted=False, is_followed=True).values()))

        # 각 키워드에 대해 db로부터 언급량 데이터 가져옴.
        temp_mention_count_dict = {}
        for idx in keyword_df.index:
            temp_mention_count_df = pd.DataFrame(list(ServiceMentionCounts.objects.filter(
                keyword_id=keyword_df["id"][idx], term_start__gt=self.start_date, term_end__lt=self.end_date).values())) # 한 키워드에 대한 언급량 데이터 목록.
            temp_mention_count_dict[keyword_df["keyword"][idx]] = temp_mention_count_df


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

        # 전체 언급량.
        total_mention = {}
        community_mention = {}
        insta_mention = {}
        blog_mention = {}
        news_mention = {}
        twitter_mention = {}
        # for keyword_key, value in temp_mention_count_dict.items():
        #     total_mention[keyword_key] = []
        #     community_mention[keyword_key] = []
        #     insta_mention[keyword_key] = []
        #     blog_mention[keyword_key] = []
        #     news_mention[keyword_key] = []
        #     twitter_mention[keyword_key] = []
        #
        #     # 데이터가 없다면 패스
        #     if value.empty == True:
        #         continue
        #
        #     # 하나의 키워드에 대해 기간 반복하여 데이터 정리.
        #     target_date = datetime.date(start_date.year, start_date.month, start_date.day)
        #     while target_date <= end_date:
        #         total_row = []
        #         community_row = []
        #         insta_row = []
        #         blog_row = []
        #         news_row = []
        #         twitter_row = []
        #
        #         total_row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         community_row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         insta_row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         blog_row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         news_row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         twitter_row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #
        #         mention_count = value[value["term_start"] == target_date.isoformat()]
        #         if mention_count.empty == True:
        #             total_row.append("null")
        #             community_row.append("null")
        #             insta_row.append("null")
        #             blog_row.append("null")
        #             news_row.append("null")
        #             twitter_row.append("null")
        #         else:
        #             total_row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["count_sum"])
        #             community_row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["community_count"])
        #             insta_row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["insta_count"])
        #             blog_row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["blog_count"])
        #             news_row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["news_count"])
        #             twitter_row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["twitter_count"])
        #
        #         total_mention[keyword_key].append(total_row)
        #         community_mention[keyword_key].append(community_row)
        #         insta_mention[keyword_key].append(insta_row)
        #         blog_mention[keyword_key].append(blog_row)
        #         news_mention[keyword_key].append(news_row)
        #         twitter_mention[keyword_key].append(twitter_row)
        #
        #         target_date += datetime.timedelta(days=1)

        # # 전체 언급량 데이터 합 구하기
        # total_mention_sum = []
        # for i in range(len(day_list)):
        #     sum = 0
        #     for keyword_key, value in total_mention.items():
        #         if len(value)-1 < i:
        #             continue
        #         temp_value = value[i][1]
        #         if temp_value!='null':
        #             sum += temp_value
        #     row = []
        #     row.append(day_list[i])
        #     row.append(sum)
        #     total_mention_sum.append(row)
        # # total_mention["total"] = total_mention_sum

        # # 커뮤니티 언급량.
        # community_mention = {}
        # for keyword_key, value in temp_mention_count_dict.items():
        #     community_mention[keyword_key] = []
        #
        #     # 데이터가 없다면 패스
        #     if value.empty == True:
        #         continue
        #
        #     # 하나의 키워드에 대해 기간 반복하여 데이터 정리.
        #     target_date = datetime.date(start_date.year, start_date.month, start_date.day)
        #     while target_date <= end_date:
        #         row = []
        #         row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         mention_count = value[value["term_start"] == target_date.isoformat()]
        #         if mention_count.empty == True:
        #             row.append("null")
        #         else:
        #             row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["community_count"])
        #         community_mention[keyword_key].append(row)
        #
        #         target_date += datetime.timedelta(days=1)
        #
        # # 전체 언급량 데이터 합 구하기
        # total_mention_sum = []
        # for i in range(len(day_list)):
        #     sum = 0
        #     for keyword_key, value in community_mention.items():
        #         if len(value) - 1 < i:
        #             continue
        #         temp_value = value[i][1]
        #         if temp_value != 'null':
        #             sum += temp_value
        #     row = []
        #     row.append(day_list[i])
        #     row.append(sum)
        #     total_mention_sum.append(row)
        # community_mention["total"] = total_mention_sum
        #
        # # 인스타 언급량.
        # insta_mention = {}
        # for keyword_key, value in temp_mention_count_dict.items():
        #     insta_mention[keyword_key] = []
        #
        #     # 데이터가 없다면 패스
        #     if value.empty == True:
        #         continue
        #
        #     # 하나의 키워드에 대해 기간 반복하여 데이터 정리.
        #     target_date = datetime.date(start_date.year, start_date.month, start_date.day)
        #     while target_date <= end_date:
        #         row = []
        #         row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         mention_count = value[value["term_start"] == target_date.isoformat()]
        #         if mention_count.empty == True:
        #             row.append("null")
        #         else:
        #             row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["insta_count"])
        #         insta_mention[keyword_key].append(row)
        #
        #         target_date += datetime.timedelta(days=1)
        #
        # # 전체 언급량 데이터 합 구하기
        # total_mention_sum = []
        # for i in range(len(day_list)):
        #     sum = 0
        #     for keyword_key, value in insta_mention.items():
        #         if len(value) - 1 < i:
        #             continue
        #         temp_value = value[i][1]
        #         if temp_value != 'null':
        #             sum += temp_value
        #     row = []
        #     row.append(day_list[i])
        #     row.append(sum)
        #     total_mention_sum.append(row)
        # # insta_mention["total"] = total_mention_sum
        #
        # # 블로그 언급량.
        # blog_mention = {}
        # for keyword_key, value in temp_mention_count_dict.items():
        #     blog_mention[keyword_key] = []
        #
        #     # 데이터가 없다면 패스
        #     if value.empty == True:
        #         continue
        #
        #     # 하나의 키워드에 대해 기간 반복하여 데이터 정리.
        #     target_date = datetime.date(start_date.year, start_date.month, start_date.day)
        #     while target_date <= end_date:
        #         row = []
        #         row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         mention_count = value[value["term_start"] == target_date.isoformat()]
        #         if mention_count.empty == True:
        #             row.append("null")
        #         else:
        #             row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["blog_count"])
        #         blog_mention[keyword_key].append(row)
        #
        #         target_date += datetime.timedelta(days=1)
        #
        # # 전체 언급량 데이터 합 구하기
        # total_mention_sum = []
        # for i in range(len(day_list)):
        #     sum = 0
        #     for keyword_key, value in blog_mention.items():
        #         if len(value) - 1 < i:
        #             continue
        #         temp_value = value[i][1]
        #         if temp_value != 'null':
        #             sum += temp_value
        #     row = []
        #     row.append(day_list[i])
        #     row.append(sum)
        #     total_mention_sum.append(row)
        # # blog_mention["total"] = total_mention_sum
        #
        # # 뉴스 언급량.
        # news_mention = {}
        # for keyword_key, value in temp_mention_count_dict.items():
        #     news_mention[keyword_key] = []
        #
        #     # 데이터가 없다면 패스
        #     if value.empty == True:
        #         continue
        #
        #     # 하나의 키워드에 대해 기간 반복하여 데이터 정리.
        #     target_date = datetime.date(start_date.year, start_date.month, start_date.day)
        #     while target_date <= end_date:
        #         row = []
        #         row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         mention_count = value[value["term_start"] == target_date.isoformat()]
        #         if mention_count.empty == True:
        #             row.append("null")
        #         else:
        #             row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["news_count"])
        #         news_mention[keyword_key].append(row)
        #
        #         target_date += datetime.timedelta(days=1)
        #
        # # 전체 언급량 데이터 합 구하기
        # total_mention_sum = []
        # for i in range(len(day_list)):
        #     sum = 0
        #     for keyword_key, value in news_mention.items():
        #         if len(value) - 1 < i:
        #             continue
        #         temp_value = value[i][1]
        #         if temp_value != 'null':
        #             sum += temp_value
        #     row = []
        #     row.append(day_list[i])
        #     row.append(sum)
        #     total_mention_sum.append(row)
        # # news_mention["total"] = total_mention_sum
        #
        # # 트위터 언급량.
        # twitter_mention = {}
        # for keyword_key, value in temp_mention_count_dict.items():
        #     twitter_mention[keyword_key] = []
        #
        #     # 데이터가 없다면 패스
        #     if value.empty == True:
        #         continue
        #
        #     # 하나의 키워드에 대해 기간 반복하여 데이터 정리.
        #     target_date = datetime.date(start_date.year, start_date.month, start_date.day)
        #     while target_date <= end_date:
        #         row = []
        #         row.append(calendar.timegm(target_date.timetuple()) * 1000)
        #         mention_count = value[value["term_start"] == target_date.isoformat()]
        #         if mention_count.empty == True:
        #             row.append("null")
        #         else:
        #             row.append(value[value["term_start"] == target_date.isoformat()].iloc[0]["twitter_count"])
        #         twitter_mention[keyword_key].append(row)
        #
        #         target_date += datetime.timedelta(days=1)
        #
        # # 전체 언급량 데이터 합 구하기
        # total_mention_sum = []
        # for i in range(len(day_list)):
        #     sum = 0
        #     for keyword_key, value in twitter_mention.items():
        #         if len(value) - 1 < i:
        #             continue
        #         temp_value = value[i][1]
        #         if temp_value != 'null':
        #             sum += temp_value
        #     row = []
        #     row.append(day_list[i])
        #     row.append(sum)
        #     total_mention_sum.append(row)
        # # twitter_mention["total"] = total_mention_sum

        context["keyword_list"] = keyword_list
        context["mention_data"] = {
            "total_mention": { "name": "전체 언급량 추이"},
            "community_mention": {"name": "커뮤니티 언급량 추이"},
            "insta_mention": {"name": "인스타 언급량 추이"},
            "blog_mention": {"name": "블로그 언급량 추이"},
            "news_mention": {"name": "뉴스 언급량 추이"},
            "twitter_mention": {"name": "트위터 언급량 추이"},
        }
        context["xaxis_day_list"] = xaxis_day_list

        # # 긍, 부정어 데이터 처리
        # df = pd.DataFrame(list(ServicePosNegWords.objects.filter(
        #     keyword_id__in=keyword_df["id"], term_start__gt=self.start_date, term_end__lt=self.end_date,
        #     term_type="W"
        # ).order_by("-word_count").values("term_start","term_end","word","word_count","rank","pos_neg","property","keyword_id")))
        #
        # pos_neg_data = {}
        # for keyword_idx in keyword_df.index:
        #     keyword_id = keyword_df["id"][keyword_idx]
        #     keyword = keyword_df["keyword"][keyword_idx]
        #
        #     pos_neg_data[keyword] = {
        #         "table": [],
        #         "wordCloud": [],
        #         "graph": {},
        #     }
        #
        #     temp_df = df[df["keyword_id"]==keyword_id]
        #     if temp_df.empty == True:
        #         continue
        #
        #     a = temp_df.groupby(["word", "pos_neg", "property"], as_index=False).sum("word_count").sort_values(by="word_count", ascending=False)
        #
        #     table_data = []
        #     wordCloud_data = []
        #     graph_data = {
        #         "pos":[],
        #         "neg":[],
        #         "neu":[],
        #     }
        #
        #     # 테이블 데이터, 워드클라우드 데이터 처리.
        #     # biggest_value = a.iloc[0]["word_count"]
        #     # div_value = 1
        #     # while (biggest_value/1000) == 0:
        #     #     div_value = div_value*10
        #     #     biggest_value = int(biggest_value/div_value)
        #
        #     for row in a.values:
        #         table_data.append(row.tolist())
        #         wordCloud_data.append([row[0], int(row[3]/10), row[1], row[3]])
        #
        #     # 그래프 데이터 처리.
        #     term_list_df = temp_df.groupby(["term_start", "term_end", "pos_neg"], as_index=False).sum("word_count").sort_values(by="term_start")
        #     for term_list_df_idx in term_list_df.index:
        #         term_start = term_list_df["term_start"][term_list_df_idx]
        #         term_end = term_list_df["term_end"][term_list_df_idx]
        #         pos_neg = term_list_df["pos_neg"][term_list_df_idx]
        #         count = term_list_df["word_count"][term_list_df_idx]
        #
        #         term_start_datetime = datetime.date(int(term_start.split("-")[0]), int(term_start.split("-")[1]), int(term_start.split("-")[2]))
        #
        #         if pos_neg=="POS":
        #             graph_data["pos"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])
        #         elif pos_neg == "NEG":
        #             graph_data["neg"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])
        #         elif pos_neg == "NEU":
        #             graph_data["neu"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])
        #
        #     pos_neg_data[keyword] = {
        #         "table": table_data,
        #         "wordCloud": wordCloud_data[:30],
        #         "graph": graph_data,
        #     }
        #
        # context["pos_neg_data"] = pos_neg_data




        # arr = []
        # for i in range(100):
        #     arr.append(["hello"+str(random.randint(0,100)), random.randint(0,100), random.randint(1000, 10000)])
        # context["sample"] = arr

        return context

def mention_data(request):
    lv1 = ""
    lv2 = ""
    mention_source = ""
    mention_source_dict = {
        "total": {"column_name": "count_sum", "ko_name": "전체"},
        "community": {"column_name": "community_count", "ko_name": "커뮤니티"},
        "insta": {"column_name": "insta_count", "ko_name": "인스타"},
        "blog": {"column_name": "blog_count", "ko_name": "블로그"},
        "news": {"column_name": "news_count", "ko_name": "뉴스"},
        "twitter": {"column_name": "twitter_count", "ko_name": "트위터"},
    }
    start_date_iso = "2021-01-01"
    end_date_iso = datetime.date.today().isoformat()

    if (request.GET.get("lv1") != None) & (request.GET.get("lv2") != None) & (request.GET.get("mention_source") != None):
        lv1 = request.GET.get("lv1")
        lv2 = request.GET.get("lv2").split("?")[0]
        mention_source = request.GET.get("mention_source")
    else:
        return

    # url 쿼리 스트링 가져오기.
    if (request.GET.get("startDate", None) != None) & (request.GET.get("endDate", None) != None):
        start_date_iso = request.GET.get("startDate")
        end_date_iso = request.GET.get("endDate")

    # lv에 해당하는 키워드 목록 가져오기.
    keyword_list = keyword_group[lv1][lv2]  # 해당하는 키워드 목록
    keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=keyword_list, is_deleted=False, is_followed=True).values()))

    # 각 키워드에 대해 db로부터 언급량 데이터 가져옴.
    temp_mention_count_dict = {}
    for idx in keyword_df.index:
        temp_mention_count_df = pd.DataFrame(list(ServiceMentionCounts.objects.filter(
            keyword_id=keyword_df["id"][idx], term_start__gt=start_date_iso, term_end__lt=end_date_iso).values()))  # 한 키워드에 대한 언급량 데이터 목록.
        temp_mention_count_dict[keyword_df["keyword"][idx]] = temp_mention_count_df

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
    for keyword_key, value in temp_mention_count_dict.items():
        total_mention[keyword_key] = []
        community_mention[keyword_key] = []
        insta_mention[keyword_key] = []
        blog_mention[keyword_key] = []
        news_mention[keyword_key] = []
        twitter_mention[keyword_key] = []

        # 데이터가 없다면 패스
        if value.empty == True:
            continue

        # 하나의 키워드에 대해 기간 반복하여 데이터 정리.
        target_date_datetime = datetime.date(start_date_datetime.year, start_date_datetime.month, start_date_datetime.day)
        while target_date_datetime <= end_date_datetime:
            total_row = []
            community_row = []
            insta_row = []
            blog_row = []
            news_row = []
            twitter_row = []

            total_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
            community_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
            insta_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
            blog_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
            news_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)
            twitter_row.append(calendar.timegm(target_date_datetime.timetuple()) * 1000)

            mention_count = value[value["term_start"] == target_date_datetime.isoformat()]
            if mention_count.empty == True:
                total_row.append("null")
                community_row.append("null")
                insta_row.append("null")
                blog_row.append("null")
                news_row.append("null")
                twitter_row.append("null")
            else:
                # row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0][mention_source_dict[mention_source]["column_name"]]))
                total_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["count_sum"]))
                community_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["community_count"]))
                insta_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["insta_count"]))
                blog_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["blog_count"]))
                news_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["news_count"]))
                twitter_row.append(int(value[value["term_start"] == target_date_datetime.isoformat()].iloc[0]["twitter_count"]))

            total_mention[keyword_key].append(total_row)
            community_mention[keyword_key].append(community_row)
            insta_mention[keyword_key].append(insta_row)
            blog_mention[keyword_key].append(blog_row)
            news_mention[keyword_key].append(news_row)
            twitter_mention[keyword_key].append(twitter_row)

            target_date_datetime += datetime.timedelta(days=1)

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
        "keyword_list": keyword_list,
        # "mention_data": {
        #     "count_list": total_mention,
        #     "name": mention_source_dict[mention_source]["ko_name"]+" 언급량 추이"
        # },
        "mention_data": {
            "total_mention": {"count_list": total_mention, "name": "전체 언급량 추이"},
            "community_mention": {"count_list": community_mention, "name": "커뮤니티 언급량 추이"},
            "insta_mention": {"count_list": insta_mention, "name": "인스타 언급량 추이"},
            "blog_mention": {"count_list": blog_mention, "name": "블로그 언급량 추이"},
            "news_mention": {"count_list": news_mention, "name": "뉴스 언급량 추이"},
            "twitter_mention": {"count_list": twitter_mention, "name": "트위터 언급량 추이"},
        },
        "xaxis_day_list": xaxis_day_list,
    }

    return JsonResponse(result);

def pos_neg_data(request):
    lv1 = ""
    lv2 = ""
    start_date_iso = "2021-01-01"
    end_date_iso = datetime.date.today().isoformat()

    if (request.GET.get("lv1") != None) & (request.GET.get("lv2") != None):
        lv1 = request.GET.get("lv1")
        lv2 = request.GET.get("lv2").split("?")[0]
    else:
        return

    # url 쿼리 스트링 가져오기.
    if (request.GET.get("startDate", None) != None) & (request.GET.get("endDate", None) != None):
        start_date_iso = request.GET.get("startDate")
        end_date_iso = request.GET.get("endDate")

    # lv에 해당하는 키워드 목록 가져오기.
    keyword_list = keyword_group[lv1][lv2]  # 해당하는 키워드 목록
    keyword_df = pd.DataFrame(list(SocialKeywords.objects.filter(keyword__in=keyword_list, is_deleted=False, is_followed=True).values()))

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
        keyword_id__in=keyword_df["id"], term_start__gt=start_date_iso, term_end__lt=end_date_iso,
        term_type="W"
    ).order_by("-word_count").values("term_start", "term_end", "word", "word_count", "rank", "pos_neg", "property", "keyword_id")))

    pos_neg_data = {}
    for keyword_idx in keyword_df.index:
        keyword_id = keyword_df["id"][keyword_idx]
        keyword = keyword_df["keyword"][keyword_idx]

        pos_neg_data[keyword] = {
            "table": [],
            "wordCloud": [],
            "graph": {},
        }

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
        term_list_df = temp_df.groupby(["term_start", "term_end", "pos_neg"], as_index=False).sum("word_count").sort_values(by="term_start")
        term_list_temp = temp_df.groupby(["term_start"], as_index=False).sum("word_count").sort_values(by="term_start")
        term_list = []
        for term in term_list_temp["term_start"].values.tolist():
            term_datetime = datetime.date(int(term.split("-")[0]), int(term.split("-")[1]), int(term.split("-")[2]))
            term_list.append(calendar.timegm(term_datetime.timetuple()) * 1000)
        graph_data["term_list"] = term_list

        for term_list_df_idx in term_list_df.index:
            term_start = term_list_df["term_start"][term_list_df_idx]
            term_end = term_list_df["term_end"][term_list_df_idx]
            pos_neg = term_list_df["pos_neg"][term_list_df_idx]
            count = int(term_list_df["word_count"][term_list_df_idx])

            term_start_datetime = datetime.date(int(term_start.split("-")[0]), int(term_start.split("-")[1]), int(term_start.split("-")[2]))

            if pos_neg == "POS":
                graph_data["pos"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])
            elif pos_neg == "NEG":
                graph_data["neg"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])
            elif pos_neg == "NEU":
                graph_data["neu"].append([calendar.timegm(term_start_datetime.timetuple()) * 1000, count])

        pos_neg_data[keyword] = {
            "table": table_data,
            "wordCloud": wordCloud_data[:30],
            "graph": graph_data,
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

            cashflow_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code_id=stock_code, subject_name="현금흐름표").values()))
            # cashflow_statement = cashflow_statement.dropna()
            cashflow_statement_account = cashflow_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

            income_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code_id=stock_code, subject_name="포괄손익계산서").values()))
            # cashflow_statement = cashflow_statement.dropna()
            income_statement_account = income_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

            balance_sheet = pd.DataFrame(list(FinancialStatement.objects.filter(code_id=stock_code, subject_name="재무상태표").values()))
            # cashflow_statement = cashflow_statement.dropna()
            balance_sheet_account = balance_sheet.groupby(["account_id", "account_level", "account_name"], as_index=False).head(1)

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

            aaa(0, income_statement, income_statement_account, "", "포괄손익계산서")
            aaa(0, balance_sheet, balance_sheet_account, "", "재무상태표")
            aaa(0, cashflow_statement, cashflow_statement_account, "", "현금흐름표")
            pass

        pass


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

company_info_view = CompanyInfoView.as_view(template_name='pages/company-info.html')
price_analysis_view = PriceAnalysisView.as_view(template_name='pages/price-analysis.html')
social_analysis_view = SocialAnalysisView.as_view(template_name='pages/social-analysis.html')
people_iframe = PeopleIframe.as_view(template_name="pages/peopleIframe.html")
