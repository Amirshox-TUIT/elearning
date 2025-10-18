from django.urls import path

from apps.blogs import views

app_name = 'blogs'

urlpatterns = [
    path('', views.PostListCreateAPIView.as_view(), name='list'),
    path('<int:pk>/', views.PostRetrieveUpdateDestroyAPIView.as_view(), name='retrieve'),

]