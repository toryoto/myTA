from django.urls import path
from . import views

app_name = 'diary'

urlpatterns = [
    path('', views.index, name='index'),  # /diary
    path('add/', views.add, name='add'),  # /diary/add
    path('update/<int:pk>/', views.update, name='update'),  # diary/update/1
    path('delete/<int:pk>/', views.delete, name='delete'),  # /diary/delete/1
    path('detail/<int:pk>/', views.detail, name='detail'),  # /diary/detail/1
]
