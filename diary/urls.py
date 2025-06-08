from django.urls import path
from . import views

app_name = 'diary'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),  # /diary
    path('add/', views.CreateView.as_view(), name='add'),  # /diary/add
    path('update/<int:pk>/', views.UpdateView.as_view(), name='update'),  # diary/update/1
    path('delete/<int:pk>/', views.DeleteView.as_view(), name='delete'),  # /diary/delete/1
    path('detail/<int:pk>/', views.DetailView.as_view(), name='detail'),  # /diary/detail/1
    path('reviewers/', views.manage_reviewers, name='manage_reviewers'),  # /diary/reviewers/
    path('reviewers/delete/<int:reviewer_id>/', views.delete_reviewer, name='delete_reviewer'),  # /diary/reviewers/delete/1/
    path('review/', views.review_list, name='review'),  # /diary/review/
]
