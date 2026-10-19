from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post/create/', views.post_create, name='post_create'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/like/', views.like_post, name='like_post'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('post/<slug:slug>/edit/', views.post_edit, name='post_edit'),
    path('post/<slug:slug>/delete/', views.post_delete, name='post_delete'),
    path('comment/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
]

