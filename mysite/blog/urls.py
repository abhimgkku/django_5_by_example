from django.urls import path
from . import views

app_name ='blog' # here we are defining namespace with app_name variable and its value is same as the name of the application.

urlpatterns = [
    path('',views.post_list,name='post_list'),
    path('<int:id>/',views.post_detail,name='post_detail')
]
