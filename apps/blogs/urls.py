from django.urls import path

from apps.blogs import views

app_name = 'blogs'

urlpatterns = [
    path('', views.PostListCreateAPIView.as_view(), name='list'),
    path('<int:pk>/', views.PostRetrieveUpdateDestroyAPIView.as_view(), name='retrieve'),
    path('<int:pk>/comments/', views.CommentListCreateAPIView.as_view(), name='comment-list'),
    path('comment/<int:pk>/', views.CommentRetrieveUpdateDestroyAPIView.as_view(), name='comment-retrieve'),
    path('<int:pk>/like/', views.LikeCreateDeleteAPIView.as_view(), name='like-create'),
]