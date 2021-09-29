import json
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import View
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from ubold.apps.models import Event
from ubold.apps.forms import EventForm

from ubold.utils.general import list_of_dict_to_list_to_obj, GenericObject
from ubold.apps.data.ecommerce import (
    ecommerceStatisticsDict, 
    transactionHistoryDict,
    recentProductsDict,
    productsDict,
    outletDict,
    productDetailDict,
    customersDict,
    ordersDict,
    orderDict,
    sellersDict,
    cartProductsDict,
    cartSummaryDict,
    cartDiscountCode,
    cartDiscountRate,
    checkoutFastDeliveryDict,
    checkoutHomeAddress,
    checkoutOfficeAddress,
    checkoutOrderDict,
    checkoutStandardDeliveryDict,
    )

User = get_user_model()

class EventListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        events = Event.objects.all()
        events_dict = []
        for event in events:
            events_dict.append(event.to_dict())
        return HttpResponse(json.dumps(events_dict), content_type='application/json')

class EventCreateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = EventForm(data=request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            save_data = {}
            save_data["title"] = cleaned_data.get("title")
            save_data["category"] = cleaned_data.get("className")
            save_data["start_date"] = cleaned_data.get("start")
            if cleaned_data.get("allDay", None):
                save_data["all_day"] = cleaned_data.get("allDay")
            if cleaned_data.get("end", None):
                save_data["end_date"] = cleaned_data.get("end")
            event = Event.objects.create(**save_data)
            return HttpResponse(json.dumps(event.to_dict()), content_type='application/json')
        return HttpResponseBadRequest(json.dumps(form.errors), content_type='application/json')

class EventUpdateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        obj = get_object_or_404(Event, id=pk)
        form = EventForm(data=request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            obj.title = cleaned_data.get("title")
            obj.category = cleaned_data.get("className")
            obj.start_date = cleaned_data.get("start")
            obj.all_day = cleaned_data.get("allDay", None)
            obj.end_date = cleaned_data.get("end", None)
            obj.save()
            return HttpResponse(json.dumps(obj.to_dict()), content_type='application/json')
        return HttpResponseBadRequest(json.dumps(form.errors), content_type='application/json')

class EventDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        pk = kwargs.get("pk", None)
        obj = get_object_or_404(Event, id=pk)
        obj.delete()
        return HttpResponse(
            json.dumps({"message" : "The event has been removed successfully."}), 
            content_type='application/json'
            )        


class AppsView(LoginRequiredMixin, TemplateView):
    pass

# calendar
apps_calendar_calendar_view = AppsView.as_view(template_name="apps/calendar/calendar.html")

#chat
apps_chat_chat_view = AppsView.as_view(template_name="apps/chat/chat.html")

# companies
apps_companies_view = AppsView.as_view(template_name="apps/companies/companies.html")

# contacts
apps_contacts_list_view = AppsView.as_view(template_name="apps/contacts/list.html")
apps_contacts_profile_view = AppsView.as_view(template_name="apps/contacts/profile.html")

# crm
apps_crm_customers_view = AppsView.as_view(template_name="apps/crm/customers.html")
apps_crm_contacts_view = AppsView.as_view(template_name="apps/crm/contacts.html")
apps_crm_dashboard_view = AppsView.as_view(template_name="apps/crm/dashboard.html")
apps_crm_leads_view = AppsView.as_view(template_name="apps/crm/leads.html")
apps_crm_opportunities_view = AppsView.as_view(template_name="apps/crm/opportunities.html")

# ecommerce

class EcommerceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statistics'] = list_of_dict_to_list_to_obj(
            ecommerceStatisticsDict)
        context['transactionHistory'] = list_of_dict_to_list_to_obj(
            transactionHistoryDict)
        context['recentProducts'] = list_of_dict_to_list_to_obj(
            recentProductsDict)
        return context
apps_ecommerce_ecommerce_dashboard_view = EcommerceDashboardView.as_view()

class EcommerceProductsView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/products.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products_list = list_of_dict_to_list_to_obj(
            productsDict)
        n = 4
        context['products'] = [products_list[i:i + n] for i in range(0, len(products_list), n)]  
        return context
apps_ecommerce_products_view = EcommerceProductsView.as_view()


class EcommerceProductDetailView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/product-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['outletData'] = list_of_dict_to_list_to_obj(outletDict)
        productDetailData = GenericObject(productDetailDict)
        context["productImages"] = productDetailData.images
        context["productDetail"] = productDetailData.detail
        return context
apps_ecommerce_products_details_view = EcommerceProductDetailView.as_view()

class EcommerceCustomersView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/customers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = list_of_dict_to_list_to_obj(customersDict)
        return context
apps_ecommerce_customers_view = EcommerceCustomersView.as_view()

class EcommerceOrdersView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/orders.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["orders"] = []
        for data in ordersDict:
            obj = GenericObject(data)
            obj.products = list_of_dict_to_list_to_obj(obj.products)
            context["orders"].append(obj)
        return context
apps_ecommerce_orders_view = EcommerceOrdersView.as_view()

class EcommerceOrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/order-detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)        
        trackerData = list_of_dict_to_list_to_obj(orderDict["trackOrderData"]["trackerData"])
        prodects = list_of_dict_to_list_to_obj(orderDict["billData"]["prodects"])
        context["order"] = GenericObject(orderDict)
        context["order"]["trackOrderData"]["trackerData"] = trackerData
        context["order"]["billData"]["prodects"] = prodects
        return context
apps_ecommerce_order_detail_view = EcommerceOrderDetailView.as_view()


class EcommerceSellersView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/sellers.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        context["sellers"] = list_of_dict_to_list_to_obj(sellersDict)
        return context
apps_ecommerce_sellers_view = EcommerceSellersView.as_view()



class EcommerceCartView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cartProducts"] = list_of_dict_to_list_to_obj(cartProductsDict)
        context["cartSummary"] = GenericObject(cartSummaryDict)
        context["cartDiscountCode"] = cartDiscountCode
        context["cartDiscountRate"] = cartDiscountRate
        return context
apps_ecommerce_cart_view = EcommerceCartView.as_view()


class EcommerceCheckoutView(LoginRequiredMixin, TemplateView):
    template_name = "apps/ecommerce/checkout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["homeAddress"] = GenericObject(checkoutHomeAddress)
        context["officeAddress"] = GenericObject(checkoutOfficeAddress)
        context["standardDelivery"] = GenericObject(checkoutStandardDeliveryDict)
        context["fastDelivery"] = GenericObject(checkoutFastDeliveryDict)
        context["order"] = GenericObject(checkoutOrderDict)
        context["order"]["products"] = list_of_dict_to_list_to_obj(checkoutOrderDict["products"])
        return context
apps_ecommerce_checkout_view = EcommerceCheckoutView.as_view()


apps_ecommerce_checkout_view = AppsView.as_view(template_name="apps/ecommerce/checkout.html")
apps_ecommerce_product_edit_view = AppsView.as_view(template_name="apps/ecommerce/product-edit.html")

# email
apps_email_inbox_view = AppsView.as_view(template_name="apps/email/inbox.html")
apps_email_read_view = AppsView.as_view(template_name="apps/email/read.html")
apps_email_compose_view = AppsView.as_view(template_name="apps/email/compose.html")
apps_email_templates_view = AppsView.as_view(template_name="apps/email/templates.html")
apps_email_templates_action_view = AppsView.as_view(template_name="apps/email/templates-action.html")
apps_email_templates_alert_view = AppsView.as_view(template_name="apps/email/templates-alert.html")
apps_email_templates_billing_view = AppsView.as_view(template_name="apps/email/templates-billing.html")

# file manager
apps_file_manager_view = AppsView.as_view(template_name="apps/manager/file-manager.html")

# projects
apps_project_create_view = AppsView.as_view(template_name="apps/project/create.html")
apps_project_detail_view = AppsView.as_view(template_name="apps/project/detail.html")
apps_project_list_view = AppsView.as_view(template_name="apps/project/list.html")

# social
apps_social_feed_view = AppsView.as_view(template_name="apps/social/feed.html")

# tasks
apps_task_details_view = AppsView.as_view(template_name="apps/task/details.html")
apps_task_kanban_board_view = AppsView.as_view(template_name="apps/task/kanban-board.html")
apps_task_list_view = AppsView.as_view(template_name="apps/task/list.html")


# tickets
apps_tickets_list_view = AppsView.as_view(template_name="apps/tickets/list.html")
apps_tickets_detail_view = AppsView.as_view(template_name="apps/tickets/detail.html")