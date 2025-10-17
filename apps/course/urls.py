from django.urls import path

from apps.course import views
from apps.reviews.views import CourseReviewListCreateView

app_name = 'courses'

urlpatterns = [
    path('', views.CourseListCreateAPIView.as_view(), name='courses'),
    path('<int:pk>/', views.CourseDetailPutPatchDeleteAPIView.as_view(), name='course-detail'),
    path('<int:pk>/reviews/', CourseReviewListCreateView.as_view(), name='course-detail'),
]