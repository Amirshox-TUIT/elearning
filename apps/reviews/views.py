from django.db.models.aggregates import Avg
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated

from apps.course.models import Course
from apps.enrolment.models import Enrollment
from apps.reviews.models import CourseReview
from apps.reviews.serializers import CourseReviewListCreateSerializer, ReviewRetrieveUpdateDestroySerializer


class CourseReviewListCreateView(ListCreateAPIView):
    queryset = CourseReview.objects.all()
    serializer_class = CourseReviewListCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        course = Course.objects.get(pk=self.kwargs['pk'])
        if self.request.user not in (enrolment.student for enrolment in course.enrollments.all()):
            raise PermissionDenied

        if self.request.user in (review.student for review in course.reviews.all()):
            raise PermissionDenied

        enrolment = Enrollment.objects.get(student=self.request.user, course=course)
        if enrolment.progress_percentage <= 20:
            raise PermissionDenied

        serializer.save(student=self.request.user, course=course)


class ReviewRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    queryset = CourseReview.objects.all()
    serializer_class = ReviewRetrieveUpdateDestroySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CourseReview.objects.filter(student=self.request.user)

    def perform_update(self, serializer):
        review = serializer.save()

        instructor = review.course.instructor
        avg_rating = CourseReview.objects.filter(course__instructor=instructor).aggregate(
            avg=Avg('rating')
        )['avg'] or 0

        instructor.rating = round(avg_rating, 2)
        instructor.save()

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)




