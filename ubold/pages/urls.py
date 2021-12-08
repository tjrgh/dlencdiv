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
    price_analysis_view, social_analysis_view,
    mention_data,
    pos_neg_data,
    people_iframe,
    price_predict_view,
    news_analysis_view,
    search_news_list,
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


    path("peopleIframe", view=people_iframe, name="people_iframe"),


    # 주가분석
    path('priceanalysis', view=price_analysis_view, name="price-analysis"),

    # 소셜분석
    path('socialanalysis', view=social_analysis_view, name="social-analysis"),
    path("ajax/socialanalysis/mentionData", mention_data, name="mention_data"),
    path("ajax/socialanalysis/posNegData", pos_neg_data, name="pos_neg_data"),

    # 주가 예측
    path("pricePredict", price_predict_view, name="price_predict"),

    # 채시보
    path("newsAnalysis", view=news_analysis_view, name="news_analysis_view"),
    path("ajax/newsList", view=search_news_list, name="search_news_list"),
]
