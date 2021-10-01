import datetime

import numpy as np
import psycopg2
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.urls import reverse
from django.views.generic import TemplateView
import pandas as pd
from ubold.common.models import Currency
from ubold.stocks.models import StockNews, FinancialStatement, HistoricData, BasicInfo, Consensus, Shareholder, Dividend
from ubold.portfolio.models import PortfolioStocks
from ubold.member.models import User
from ubold.dart.models import CorpCodeData, DartSearchData

User = get_user_model()

class ComponentsView(LoginRequiredMixin, TemplateView):
    stock_code = ""

    # def get(self,request, *args, **kwargs):
    #     request.GET.
        # if len(request.GET)!=0:
        #     self.stock_code = request.GET["code"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result_list = []

        # code 인자 확인
        if "code" in kwargs:
            self.stock_code = kwargs["code"]

        today = datetime.date.today()
        if today.weekday() > 4:#오늘이 토,일요일이라면
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
        stock_list = pd.read_sql("select * from stocks_basic_info where corp_code!=' ' "
                                 "and code='A000020' "
                                 "order by code", db)
        fin_list = pd.read_sql("select "
                                "  code_id, this_term_name, subject_name, account_id, this_term_amount "
                                "from stock_financial_statement fs "
                                "where "
                                "  ((subject_name='재무상태표' and (account_id='8111' or account_id='8900')) "
                                "  or (subject_name='포괄손익계산서' and (account_id='1100' or account_id='8200'))) "
                                "  and this_term_name = (select max(this_term_name) from stock_financial_statement fs2 where fs2.code_id = fs.code_id) "
                                "  and code_id='A000020'  "
                                "", db)\
                    .sort_values(by="code_id")
        price_list = pd.read_sql("select * "
                                 "from stocks_historic_data hd "
                                 "where hd.date='"+today+"' or hd.date='"+yesterday+"' "
                                 "  and code_id='A000020'"
                                 "  ", db).sort_values(by="code_id")

        for index, stock in stock_list.iterrows():
            code = stock["code"]
            # 발행 주식수
            stock_count = fin_list.loc[(fin_list["subject_name"]=="재무상태표") & (fin_list["account_id"]=="8111") & (fin_list["code_id"]==code)]
            if (stock_count.empty == True) or (np.isnan(stock_count.iloc[0]["this_term_amount"])):
                stock_count = None
            else:
                stock_count = stock_count.iloc[0]["this_term_amount"]
            # 오늘 주가
            today_price = price_list.loc[(price_list["code_id"]==code) & (price_list["date"]==datetime.date.fromisoformat(today))]
            if (today_price.empty == True) or (np.isnan(today_price.iloc[0]["close_price"])):
                today_price = None
            else:
                today_price = today_price.iloc[0]["close_price"]
            # 어제 주가
            yesterday_price = price_list.loc[(price_list["code_id"]==code) & (price_list["date"]==datetime.date.fromisoformat(yesterday))]
            if (yesterday_price.empty == True) or (np.isnan(yesterday_price.iloc[0]["close_price"])):
                yesterday_price = None
            else:
                yesterday_price = yesterday_price.iloc[0]["close_price"]
            # 거래량
            trade_volume = price_list.loc[(price_list["code_id"]==code) & (price_list["date"]==datetime.date.fromisoformat(today))]
            if (trade_volume.empty==True) or (np.isnan(trade_volume.iloc[0]["transaction_volume"])):
                trade_volume = None
            else:
                trade_volume = trade_volume.iloc[0]["transaction_volume"]
            #매출액
            profit = fin_list.loc[(fin_list["code_id"]==code) & (fin_list["subject_name"]=="포괄손익계산서") & (fin_list["account_id"]=="1100")]
            if (profit.empty == True) or (np.isnan(profit.iloc[0]["this_term_amount"])):
                profit = None
            else:
                profit = profit.iloc[0]["this_term_amount"]
            # 당기순이익
            net_income =fin_list.loc[(fin_list["code_id"]==code) & (fin_list["subject_name"]=="포괄손익계산서") & (fin_list["account_id"]=="8200")]
            if (net_income.empty == True) or (np.isnan(net_income.iloc[0]["this_term_amount"])):
                net_income = None
            else:
                net_income = net_income.iloc[0]["this_term_amount"]
            # 순자산
            total_capital = fin_list.loc[(fin_list["subject_name"]=="재무상태표") & (fin_list["account_id"]=="8900") & (fin_list["code_id"]==code)]
            if (total_capital.empty == True) or (np.isnan(total_capital.iloc[0]["this_term_amount"])):
                total_capital = None
            else:
                total_capital = total_capital.iloc[0]["this_term_amount"]

            if (stock_count == None) or (today_price== None):
                market_cap = None
            else:
                market_cap = format(int(stock_count*today_price),",d") #시가총액

            if (stock_count == None) or (today_price== None) or (profit==None):
                psr = None
            else:
                psr = round(stock_count*today_price/profit,2)

            if (stock_count == None) or (today_price== None) or (net_income==None):
                per = None
            else:
                per = round(today_price/(net_income/stock_count),2)

            if (net_income == None) or (stock_count== None):
                eps = None
            else:
                eps = round(net_income/stock_count,2)

            if (per == None) or (eps== None):
                peg = None
            else:
                peg = round(per/eps,2)

            if (total_capital == None) or (stock_count== None):
                bps = None
            else:
                bps = round(total_capital / stock_count,2)

            if (bps == None) or (today_price== None):
                pbr = None
            else:
                pbr = round(today_price / bps, 2)

            if (net_income == None) or (total_capital== None):
                roe = None
            else:
                roe = round(net_income / total_capital, 2)

            if (today_price==None) or (yesterday_price==None):
                price_rate = None
            else:
                price_rate = round(today_price/yesterday_price, 2)

            if today_price != None:
                today_price = format(int(today_price), ",d")
            if trade_volume != None:
                trade_volume = format(int(trade_volume), ",d")
            row = [stock["name"], market_cap, today_price, price_rate, trade_volume, psr, per, peg, pbr, eps, roe, code ]
            result_list.append(row)

        context["stock_data_list"] = result_list

        #
        # 종목 리스트
        stock_list = BasicInfo.objects.exclude(corp_code=' ')

        if self.stock_code!="":
            # 주가 데이터 가져오기.
            trade_data_list = HistoricData.objects.filter(code=self.stock_code)
            close_price_list = list(HistoricData.objects.filter(code=self.stock_code).values_list("close_price", flat=True))
            close_price_list = [int(x) for x in close_price_list]
            trade_volume_list = list(HistoricData.objects.filter(code=self.stock_code).values_list("transaction_volume", flat=True))


            context["close_price_list"] = close_price_list
            context["trade_volume_list"] = trade_volume_list

            # 재무 데이터
            income_statement = pd.DataFrame(list(FinancialStatement.objects.filter(code=self.stock_code, subject_name="포괄손익계산서").values()))
            income_statement = income_statement.dropna()
            income_statement_account = income_statement.groupby(["account_id", "account_level", "account_name"], as_index=False).all() # 항목 리스트.

            term_list = FinancialStatement.objects.filter(code=self.stock_code).order_by("this_term_name")\
                .values("this_term_name").annotate(Count("this_term_name"))
            term_list = [x["this_term_name"] for x in term_list]

            def aaa(lv, original_df, part_df, term_list, ):
                result = {}
                lv_0_list = part_df[part_df["account_level"] == lv]  # 항목 리스트 중 lv 0 리스트.
                for index, lv_0 in lv_0_list.iterrows():
                    # 해당 항목 row 추가
                    row = {}
                    for term in term_list:
                        value = original_df[(original_df["this_term_name"] == term) & (original_df["account_id"] == lv_0["account_id"])]
                        if value.empty == True:
                            row[term] = ""
                        else:
                            row[term] = format(int(value.iloc[0]["this_term_amount"]), ",d")
                    lv_0_account_name = lv_0["account_name"].split("_")[lv]
                    result[lv_0_account_name] = row
                    # 해당 항목의 하위 항목들 추출.
                    lv_0_low_list = pd.DataFrame(columns=part_df.columns)
                    for index, r in part_df.iterrows():
                        if (lv_0_account_name == r["account_name"].split("_")[lv]) & (r["account_level"] > lv):
                            lv_0_low_list = pd.DataFrame.append(lv_0_low_list, r)
                    if len(lv_0_low_list) <= 0:
                        continue
                    # lv_1_list = lv_0_low_list[lv_0_low_list["account_level"] == (lv+1)]

                    result.update(aaa(lv+1, original_df, lv_0_low_list, term_list))

                return result

            income_statement_list = aaa(0, income_statement, income_statement_account, term_list)
            # 재무 데이터 정렬
            # income_statement_list = {}
            # lv_0_list = income_statement_account[income_statement_account["account_level"]==0] # 항목 리스트 중 lv 0 리스트.
            # for index, lv_0 in lv_0_list.iterrows():
            #     # 해당 항목 row 추가
            #     row = {}
            #     for term in term_list:
            #         value = income_statement[(income_statement["this_term_name"]==term) & (income_statement["account_id"]==lv_0["account_id"])]
            #         if value.empty==True:
            #             row[term] = ""
            #         else:
            #             row[term] = format(int(value.iloc[0]["this_term_amount"]),",d")
            #     lv_0_account_name = lv_0["account_name"].split("_")[0]
            #     income_statement_list[lv_0_account_name] = (row)
            #     # 해당 항목의 하위 row 반복
            #     lv_0_low_list = pd.DataFrame(columns=income_statement_account.columns)
            #     for index, r in income_statement_account.iterrows():
            #         if lv_0_account_name == r["account_name"].split("_")[0]:
            #             lv_0_low_list = pd.DataFrame.append(lv_0_low_list, r)
            #     if lv_0_low_list.empty==True:
            #         continue
            #     lv_1_list = lv_0_low_list[lv_0_low_list["account_level"]==1]
            #     for index, lv_1 in lv_1_list.iterrows():
            #         # 해당 항목 row 추가
            #         row = {}
            #         for term in term_list:
            #             value = income_statement[(income_statement["this_term_name"] == term) & (income_statement["account_id"] == lv_1["account_id"])]
            #             if (value.empty == True):
            #                 row[term] = ("")
            #             else:
            #                 row[term] = format(int(value.iloc[0]["this_term_amount"]),",d")
            #
            #         lv_1_account_name = lv_1["account_name"].split("_")[1]
            #
            #         income_statement_list[lv_1_account_name] = (row)
            #
            #         # 해당 항목의 하위 row 반복
            #         lv_1_low_list = pd.DataFrame(columns=lv_0_low_list.columns)
            #         for index, r in lv_0_low_list.iterrows():
            #             if lv_1_account_name == r["account_name"].split("_")[0]:
            #                 lv_1_low_list = pd.DataFrame.append(lv_1_low_list, r)
            #         if lv_1_low_list.empty == True:
            #             continue
            #         lv_2_list = lv_1_low_list[lv_1_low_list["account_level"] == 2]

            context["income_statement"] = income_statement_list
            context["income_statement_term_list"] = term_list

            # 증권사 컨센서스
            Consensus.objects.filter(code_id=self.stock_code)

            # 공시
            if "notice_year" in kwargs:
                notice_year = kwargs["notice_year"]
            else:
                notice_year = str(datetime.date.today().year)
            notice_list = DartSearchData.objects.filter(
                stock_code='347860', data_date__gt=notice_year+"-01-01", data_date__lt=notice_year+"-12-31"
            ).order_by("-data_date")

            context["notice_list"] = notice_list

            # 주주정보
            shareholder_list_data = {}
            shareholder_list_df = pd.DataFrame(list(Shareholder.objects.filter(code_id=self.stock_code).values()))
            shareholder_list_df = shareholder_list_df.dropna()
            shareholder_name_list = shareholder_list_df.groupby(["shareholder_name"], as_index=False).all()

            term_list = Shareholder.objects.filter(code=self.stock_code).order_by("term_name") \
                .values("term_name").annotate(Count("term_name"))
            term_list = [x["term_name"] for x in term_list]

            for shareholder_name in shareholder_name_list["shareholder_name"]:
                shareholder_list_df[shareholder_list_df["shareholder_name"]==shareholder_name]
                row = {}
                for term in term_list:
                    value = shareholder_list_df[(shareholder_list_df["term_name"] == term) & (shareholder_list_df["shareholder_name"] == shareholder_name)]
                    if value.empty == True:
                        row[term] = ""
                    else:
                        row[term] = value.iloc[0]["share_per"]
                shareholder_list_data[shareholder_name] = row

            context["shareholder_list"] = shareholder_list_data
            context["shareholder_term_list"] = term_list

            # 배당 정보
            dividend_list_data = {}
            dividend_list_df = pd.DataFrame(list(Dividend.objects.filter(code_id=self.stock_code).values()))
            dividend_list_df = dividend_list_df.dropna()
            dividend_name_list = dividend_list_df.groupby(["account_name"], as_index=False).all()

            term_list = Dividend.objects.filter(code=self.stock_code).order_by("term_name") \
                .values("term_name").annotate(Count("term_name"))
            term_list = [x["term_name"] for x in term_list]

            for account_name in dividend_name_list["account_name"]:
                dividend_list_df[dividend_list_df["account_name"] == account_name]
                row = {}
                for term in term_list:
                    value = dividend_list_df[(dividend_list_df["term_name"] == term) & (dividend_list_df["account_name"] == account_name)]
                    if value.empty == True:
                        row[term] = ""
                    else:
                        row[term] = value.iloc[0]["value"]
                dividend_list_data[account_name] = row

            context["dividend_list"] = dividend_list_data
            context["dividend_term_list"] = term_list

        return context

    pass

# ecommerce
components_base_ui_tabs_accordions_view = ComponentsView.as_view(template_name="components/base-ui/tabs-accordions.html")
components_base_ui_avatars_view = ComponentsView.as_view(template_name="components/base-ui/avatars.html")
components_base_ui_buttons_view = ComponentsView.as_view(template_name="components/base-ui/buttons.html")
components_base_ui_cards_view = ComponentsView.as_view(template_name="components/base-ui/cards.html")
components_base_ui_carousel_view = ComponentsView.as_view(template_name="components/base-ui/carousel.html")
components_base_ui_dropdowns_view = ComponentsView.as_view(template_name="components/base-ui/dropdowns.html")
components_base_ui_video_view = ComponentsView.as_view(template_name="components/base-ui/video.html")
components_base_ui_general_view = ComponentsView.as_view(template_name="components/base-ui/general.html")
components_base_ui_grid_view = ComponentsView.as_view(template_name="components/base-ui/grid.html")
components_base_ui_images_view = ComponentsView.as_view(template_name="components/base-ui/images.html")
components_base_ui_list_group_view = ComponentsView.as_view(template_name="components/base-ui/list-group.html")
components_base_ui_modals_view = ComponentsView.as_view(template_name="components/base-ui/modals.html")
components_base_ui_notifications_view = ComponentsView.as_view(template_name="components/base-ui/notifications.html")
components_base_ui_tooltips_popovers_view = ComponentsView.as_view(template_name="components/base-ui/tooltips-popovers.html")
components_base_ui_portlets_view = ComponentsView.as_view(template_name="components/base-ui/portlets.html")
components_base_ui_progress_view = ComponentsView.as_view(template_name="components/base-ui/progress.html")
components_base_ui_ribbons_view = ComponentsView.as_view(template_name="components/base-ui/ribbons.html")
components_base_ui_spinners_view = ComponentsView.as_view(template_name="components/base-ui/spinners.html")
components_base_ui_typography_view = ComponentsView.as_view(template_name="components/base-ui/typography.html")
components_base_ui_offcanvas_view = ComponentsView.as_view(template_name="components/base-ui/offcanvas.html")


# extended
components_extended_dragula_view = ComponentsView.as_view(template_name="components/extended/dragula.html")
components_extended_nestable_view = ComponentsView.as_view(template_name="components/extended/nestable.html")
components_extended_range_slider_view = ComponentsView.as_view(template_name="components/extended/range-slider.html")
components_extended_animation_view = ComponentsView.as_view(template_name="components/extended/animation.html")
components_extended_sweet_alert_view = ComponentsView.as_view(template_name="components/extended/sweet-alert.html")
components_extended_tour_view = ComponentsView.as_view(template_name="components/extended/tour.html")
components_extended_scrollspy_view = ComponentsView.as_view(template_name="components/extended/scrollspy.html")
components_extended_loading_buttons_view = ComponentsView.as_view(template_name="components/extended/loading-buttons.html")

# widgets
components_widgets_view = ComponentsView.as_view(template_name="components/widgets.html")

# icons
components_icons_two_tone_view = ComponentsView.as_view(template_name="components/icons/two-tone.html")
components_icons_feather_view = ComponentsView.as_view(template_name="components/icons/feather.html")
components_icons_mdi_view = ComponentsView.as_view(template_name="components/icons/mdi.html")
components_icons_dripicons_view = ComponentsView.as_view(template_name="components/icons/dripicons.html")
components_icons_font_awesome_view = ComponentsView.as_view(template_name="components/icons/font-awesome.html")
components_icons_themify_view = ComponentsView.as_view(template_name="components/icons/themify.html")
components_icons_simple_line_view = ComponentsView.as_view(template_name="components/icons/simple-line.html")
components_icons_weather_view = ComponentsView.as_view(template_name="components/icons/weather.html")

# forms
components_forms_elements_view = ComponentsView.as_view(template_name="components/forms/elements.html")
components_forms_advanced_view = ComponentsView.as_view(template_name="components/forms/advanced.html")
components_forms_validation_view = ComponentsView.as_view(template_name="components/forms/validation.html")
components_forms_pickers_view = ComponentsView.as_view(template_name="components/forms/pickers.html")
components_forms_wizard_view = ComponentsView.as_view(template_name="components/forms/wizard.html")
components_forms_masks_view = ComponentsView.as_view(template_name="components/forms/masks.html")
components_forms_quilljs_view = ComponentsView.as_view(template_name="components/forms/quilljs.html")
components_forms_file_uploads_view = ComponentsView.as_view(template_name="components/forms/file-uploads.html")
components_forms_x_editable_view = ComponentsView.as_view(template_name="components/forms/x-editable.html")
components_forms_image_crop_view = ComponentsView.as_view(template_name="components/forms/image-crop.html")



# charts
components_charts_apex_view = ComponentsView.as_view(template_name="components/charts/apex.html")
components_charts_flot_view = ComponentsView.as_view(template_name="components/charts/flot.html")
components_charts_morris_view = ComponentsView.as_view(template_name="components/charts/morris.html")
components_charts_chartjs_view = ComponentsView.as_view(template_name="components/charts/chartjs.html")
components_charts_peity_view = ComponentsView.as_view(template_name="components/charts/peity.html")
components_charts_chartist_view = ComponentsView.as_view(template_name="components/charts/chartist.html")
components_charts_c3_view = ComponentsView.as_view(template_name="components/charts/c3.html")
components_charts_sparklines_view = ComponentsView.as_view(template_name="components/charts/sparklines.html")
components_charts_knob_view = ComponentsView.as_view(template_name="components/charts/knob.html")


# tables
components_tables_basic_view = ComponentsView.as_view(template_name="components/tables/basic.html")
components_tables_datatables_view = ComponentsView.as_view(template_name="components/tables/datatables.html")
components_tables_editable_view = ComponentsView.as_view(template_name="components/tables/editable.html")
components_tables_responsive_view = ComponentsView.as_view(template_name="components/tables/responsive.html")
components_tables_footables_view = ComponentsView.as_view(template_name="components/tables/footables.html")
components_tables_bootstrap_view = ComponentsView.as_view(template_name="components/tables/bootstrap.html")
components_tables_tablesaw_view = ComponentsView.as_view(template_name="components/tables/tablesaw.html")
components_tables_jsgrid_view = ComponentsView.as_view(template_name="components/tables/jsgrid.html")

# maps
components_maps_google_view = ComponentsView.as_view(template_name="components/maps/google.html")
components_maps_vector_view = ComponentsView.as_view(template_name="components/maps/vector.html")
components_maps_mapael_view = ComponentsView.as_view(template_name="components/maps/mapael.html")

test = ComponentsView.as_view(template_name="components/tables/test.html")
