from django.conf.urls import url

from usaspending_api.accounts.views import federal_accounts_v2 as views

# bind ViewSets to URLs
object_class_federal_accounts = views.ObjectClassFederalAccountsViewSet.as_view()
description_federal_accounts = views.DescriptionFederalAccountsViewSet.as_view()
sankey_federal_accounts = views.SankeyFederalAccountsViewSet.as_view()


urlpatterns = [
    url(r'(?P<pk>[0-9]+)/available_object_classes$', object_class_federal_accounts),
    url(r'(?P<pk>[0-9]+)/description$', description_federal_accounts),
    url(r'(?P<pk>[0-9]+)/sankey$', sankey_federal_accounts),
]
