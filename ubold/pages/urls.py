from django.urls import path


from .views import (

    custom_pages_coming_soon_view,
    custom_pages_faqs_view,
    custom_pages_gallery_view,
    custom_pages_invoice_view,
    custom_pages_maintenance_view,
    custom_pages_pricing_view,
    custom_pages_search_results_view,
    custom_pages_sitemap_view,
    custom_pages_starter_view,
    custom_pages_timeline_view,
    custom_pages_404_alt_view,
    custom_pages_404_two_view,
    custom_pages_404_view,
    custom_pages_500_two_view,
    custom_pages_500_view,
    company_info_view,
    price_analysis_view, social_analysis_view,
    mention_data,
    pos_neg_data,
    company_info_price_data,
    company_info_financial_graph_data,
    company_info_income_statement_table_data,
    company_info_balance_sheet_table_data,
    company_info_cashflow_table_data,
    company_info_notice,
    company_info_shareholder,
    company_info_dividend,
    company_info_wcp,
    company_info_staff_number,
    company_info_bm_average_wage,
    company_info_board_member,
    company_info_bm_personal_wage,
    people_iframe,
    price_predict_view,

)


app_name = "pages"
urlpatterns = [

    # pages
    path("coming-soon", view=custom_pages_coming_soon_view, name="coming-soon"),
    path("faqs", view=custom_pages_faqs_view, name="faqs"),
    path("gallery", view=custom_pages_gallery_view, name="gallery"),
    path("invoice", view=custom_pages_invoice_view, name="invoice"),
    path("maintenance", view=custom_pages_maintenance_view, name="maintenance"),
    path("pricing", view=custom_pages_pricing_view, name="pricing"),
    path("search-results", view=custom_pages_search_results_view, name="search-results"),
    path("sitemap", view=custom_pages_sitemap_view, name="sitemap"),
    path("starter", view=custom_pages_starter_view, name="starter"),
    path("timeline", view=custom_pages_timeline_view, name="timeline"),
    path("404-alt", view=custom_pages_404_alt_view, name="404-alt"),
    path("404-two", view=custom_pages_404_two_view, name="404-two"),
    path("404", view=custom_pages_404_view, name="404"),
    path("500", view=custom_pages_500_view, name="500"),
    path("500-two", view=custom_pages_500_two_view, name="500-two"),

    # company info
    path('companyinfo', view=company_info_view, name='company-info'),
    path("companyinfo/<str:code>", view=company_info_view, name="company-info-detail"),
    path("ajax/companyinfo/priceData", view=company_info_price_data, name="company-info-price-data"),
    path("ajax/companyinfo/financialGraphData", view=company_info_financial_graph_data, name="company_info_financial_graph_data"),
    path("ajax/companyinfo/incomeStatement", view=company_info_income_statement_table_data , name="company_info_income_statement_table_data"),
    path("ajax/companyinfo/balanceSheet", view=company_info_balance_sheet_table_data , name="company_info_balance_sheet_table_data"),
    path("ajax/companyinfo/cashflow", view=company_info_cashflow_table_data , name="company_info_cashflow_table_data"),
    path("ajax/companyinfo/notice", view=company_info_notice , name="company_info_notice"),
    path("ajax/companyinfo/shareholder", view=company_info_shareholder , name="company_info_shareholder"),
    path("ajax/companyinfo/dividend", view=company_info_dividend , name="company_info_dividend"),
    path("ajax/companyinfo/workerCountPay", view=company_info_wcp , name="company_info_wcp"),
    path("ajax/companyinfo/staffNumber", view=company_info_staff_number , name="company_info_staff_number"),
    path("ajax/companyinfo/boardMemberAverageWage", view=company_info_bm_average_wage , name="company_info_bm_average_wage"),
    path("ajax/companyinfo/boardMember", view=company_info_board_member , name="company_info_board_member"),
    path("ajax/companyinfo/boardMemberPersonalWage", view=company_info_bm_personal_wage , name="company_info_bm_personal_wage"),

    path("peopleIframe", view=people_iframe, name="people_iframe"),


    # 주가분석
    path('priceanalysis', view=price_analysis_view, name="price-analysis"),

    # 소셜분석
    path('socialanalysis/<str:lv1>/<str:lv2>', view=social_analysis_view, name="social-analysis"),
    path("ajax/socialanalysis/mentionData", mention_data, name="mention_data"),
    path("ajax/socialanalysis/posNegData", pos_neg_data, name="pos_neg_data"),

    # 주가 예측
    path("pricePredict", price_predict_view, name="price_predict")
]
