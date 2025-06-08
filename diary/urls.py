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
    path('review/', views.review_list, name='review'),  # /diary/review/
    # HTMX用のURL
    path('htmx/comment/<int:day_id>/', views.add_comment_htmx, name='add_comment_htmx'),  # /diary/htmx/comment/1/
    path('htmx/reviewer/add/', views.add_reviewer_htmx, name='add_reviewer_htmx'),  # /diary/htmx/reviewer/add/
    path('htmx/reviewer/delete/<int:reviewer_id>/', views.delete_reviewer_htmx, name='delete_reviewer_htmx'),  # /diary/htmx/reviewer/delete/1/
]