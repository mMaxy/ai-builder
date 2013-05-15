from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static
#from django.views.generic import DetailView, ListView
from ai import views


urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^(?P<nw_id>\d+)/$', views.details, name = 'details'),
    url(r'^upload/$', views.upload, name = 'upload'),
)