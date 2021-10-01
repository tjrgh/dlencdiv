from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count

from ubold.stocks.models import FinancialStatement, HistoricData, BasicInfo
from ubold.dart.models import DartSearchData

import numpy as np
import pandas as pd
import psycopg2
import datetime

User = get_user_model()


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result_list = []

        # code 인자 확인
        if "code" in kwargs:
            self.stock_code = kwargs["code"]

        today = datetime.date.today()
        if today.weekday() > 4:  # 오늘이 토,일요일이라면
            today = today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=4)
            today = today.isoformat()
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        if yesterday.weekday() > 4:
            yesterday = yesterday - datetime.timedelta(days=yesterday.weekday()) + datetime.timedelta(days=4)
            yesterday = yesterday.isoformat()
        today = "2021-09-13"
        yesterday = "2021-09-10"

        db = psycopg2.connect(host="112.220.72.179", dbname="openmetric", user="openmetric",
                              password=")!metricAdmin01", port=2345)
        cur = db.cursor()
        stock_list = pd.read_sql(
            "select * from stocks_basic_info where corp_code!=' ' and code='A000020' order by code", db)
        fin_list = pd.read_sql("select "
                               "  code_id, this_term_name, subject_name, account_id, this_term_amount "
                               "from stock_financial_statement fs "
                               "where "
                               "  ((subject_name='재무상태표' and (account_id='8111' or account_id='8900')) "
                               "  or (subject_name='포괄손익계산서' and (account_id='1100' or account_id='8200'))) "
                               "  and this_term_name = (select max(this_term_name) from stock_financial_statement fs2 where fs2.code_id = fs.code_id)"
                               "  and code_id='A000020'  ", db) \
            .sort_values(by="code_id")
        price_list = pd.read_sql("select * "
                                 "from stocks_historic_data hd "
                                 "where hd.date='" + today + "' or hd.date='" + yesterday + "' "
                                                                                            "  and code_id='A000020'"
                                                                                            "  ", db).sort_values(
            by="code_id")

        for index, stock in stock_list.iterrows():
            code = stock["code"]
            # 발행 주식수
            stock_count = fin_list.loc[(fin_list["subject_name"] == "재무상태표") & (fin_list["account_id"] == "8111") & (
                    fin_list["code_id"] == code)]
            if (stock_count.empty == True) or (np.isnan(stock_count.iloc[0]["this_term_amount"])):
                stock_count = None
            else:
                stock_count = stock_count.iloc[0]["this_term_amount"]
            # 오늘 주가
            today_price = price_list.loc[
                (price_list["code_id"] == code) & (price_list["date"] == datetime.date.fromisoformat(today))]
            if (today_price.empty == True) or (np.isnan(today_price.iloc[0]["close_price"])):
                today_price = None
            else:
                today_price = today_price.iloc[0]["close_price"]
            # 어제 주가
            yesterday_price = price_list.loc[
                (price_list["code_id"] == code) & (price_list["date"] == datetime.date.fromisoformat(yesterday))]
            if (yesterday_price.empty == True) or (np.isnan(yesterday_price.iloc[0]["close_price"])):
                yesterday_price = None
            else:
                yesterday_price = yesterday_price.iloc[0]["close_price"]
            # 거래량
            trade_volume = price_list.loc[
                (price_list["code_id"] == code) & (price_list["date"] == datetime.date.fromisoformat(today))]
            if (trade_volume.empty == True) or (np.isnan(trade_volume.iloc[0]["transaction_volume"])):
                trade_volume = None
            else:
                trade_volume = trade_volume.iloc[0]["transaction_volume"]
            # 매출액
            profit = fin_list.loc[(fin_list["code_id"] == code) & (fin_list["subject_name"] == "포괄손익계산서") & (
                    fin_list["account_id"] == "1100")]
            if (profit.empty == True) or (np.isnan(profit.iloc[0]["this_term_amount"])):
                profit = None
            else:
                profit = profit.iloc[0]["this_term_amount"]
            # 당기순이익
            net_income = fin_list.loc[(fin_list["code_id"] == code) & (fin_list["subject_name"] == "포괄손익계산서") & (
                    fin_list["account_id"] == "8200")]
            if (net_income.empty == True) or (np.isnan(net_income.iloc[0]["this_term_amount"])):
                net_income = None
            else:
                net_income = net_income.iloc[0]["this_term_amount"]
            # 순자산
            total_capital = fin_list.loc[(fin_list["subject_name"] == "재무상태표") & (fin_list["account_id"] == "8900") & (
                    fin_list["code_id"] == code)]
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

        if self.stock_code != "":
            # 주가 데이터 가져오기.
            trade_data_list = HistoricData.objects.filter(code=self.stock_code)
            close_price_list = list(
                HistoricData.objects.filter(code=self.stock_code).values_list("close_price", flat=True))
            close_price_list = [int(x) for x in close_price_list]
            trade_volume_list = list(
                HistoricData.objects.filter(code=self.stock_code).values_list("transaction_volume", flat=True))

            context["close_price_list"] = close_price_list
            context["trade_volume_list"] = trade_volume_list
            context["comp_name"] = BasicInfo.objects.get(code=self.stock_code).name

            # 재무 데이터
            income_statement = pd.DataFrame(
                list(FinancialStatement.objects.filter(code=self.stock_code, subject_name="포괄손익계산서").values()))
            income_statement_account = income_statement.groupby(["account_id", "account_level", "account_name"],
                                                                as_index=False).all()

            term_list = FinancialStatement.objects.filter(code=self.stock_code) \
                .values("this_term_name").annotate(Count("this_term_name"))
            term_list = [x["this_term_name"] for x in term_list]

            # 재무 데이터 정렬
            # income_statement_list = []
            # lv_0_list = income_statement_account[income_statement_account["account_level"]==0]
            # for lv_0 in lv_0_list:
            #     # 해당 항목 row 추가
            #     for term in term_list:
            #
            #         income_statement_list.append(income_statement[(income_statement["this_term_name"]==term) & (income_statement["account_id"]==lv_0["account_id"])])
            #
            #     # 해당 항목의 하위 row 반복
            #     lv_0_account_name = lv_0["account_name"]
            #     lv_0_low_list = income_statement_account[lv_0_account_name in income_statement_account["account_name"].split("_")]
            #     lv_1_list = income_statement_account[lv_0_low_list["account_level"]==1]
            #     for lv_1 in lv_1_list:
            #         lv_1_account_name = lv_1["account_name"]
            #         lv_1_low_list = lv_0_low_list[lv_1_account_name in lv_0_low_list["account_name"].split("_")]
            #         lv_2_list = lv_1_low_list[lv_1_low_list["account_level"] == 2]
            #         for lv_2 in lv_2_list:
            #             lv_2_account_name = lv_2["account_name"]
            #             lv_2_low_list = lv_1_low_list[lv_2_account_name in lv_1_low_list["account_name"].split("_")]
            #             if lv_2_low_list.empty==True:
            #                 break
            #             lv_3_list = lv_2_low_list[lv_2_low_list["account_level"] == 3]

            context["income_statement"] = income_statement
            context["income_statement_term_list"] = term_list

        return context


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
