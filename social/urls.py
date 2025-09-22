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
]

