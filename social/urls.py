from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),  
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path("feed/", views.feed, name="feed"),
    path("like/<int:post_id>/", views.like_post, name="like_post"),
    path("follow/<str:username>/", views.toggle_follow, name="toggle_follow"),
    path("comment/<int:post_id>/", views.add_comment, name="add_comment"),
    path("notifications/", views.notifications_view, name="notifications"),
    path('notifications/count/', views.unread_notifications_count, name='unread_notifications_count'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
] 







