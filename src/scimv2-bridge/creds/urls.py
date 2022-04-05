from django.urls import path

from creds import views

urlpatterns = [
    path('simple_pwd', views.SimplePwdView.as_view(), name='simple_pwd'),
]
