from django.conf.urls import patterns, include, url
import web


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'phl_bike_thefts.views.home', name='home'),
    # url(r'^phl_bike_thefts/', include('phl_bike_thefts.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the a   dmin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'refresh', "web.views.refresh"),
    url(r'search', "web.views.search"),
    url(r'', "web.views.index"),

)
