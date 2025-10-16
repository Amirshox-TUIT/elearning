from django.urls import path

from apps.course import views

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListCreateAPIView.as_view(), name='courses'),
    path('<int:pk>/', views.CourseDetailPutPatchDeleteAPIView.as_view(), name='course-detail'),
]