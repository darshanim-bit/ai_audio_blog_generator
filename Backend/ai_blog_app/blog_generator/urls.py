"""Setting up the URLs patterns for Blog Generator
"""
from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.user_login, name='login'),
    path('logout', views.user_logout, name='logout'),
    path('signup', views.user_signup, name='signup'),
    path('generate-blog', views.generate_blog, name='generate-blog'),
    path('all-blogs', views.blog_list, name='all-blogs'),
    path('blog-detail/<int:blog_id>', views.blog_detail, name='blog-detail'),
    
    ]


