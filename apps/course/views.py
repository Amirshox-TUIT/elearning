from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.course.models import Course
from apps.course.serializers import CourseListCreateSerializer, CourseDetailSerializer


class CourseListCreateAPIView(APIView):
    serializer_class = CourseListCreateSerializer
    model = Course

    def get_object(self, request):
        courses = self.model.objects.filter(status='published')
        cat_id = request.GET.get('cat_id')
        level = request.GET.get('level')
        instructor_id = request.GET.get('instructor_id')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        is_featured = request.GET.get('is_featured')
        language = request.GET.get('language')
        search = request.GET.get('search')
        ordering = request.GET.get('ordering')

        if cat_id:
            courses = courses.filter(category_id=cat_id)

        if level:
            courses = courses.filter(level=level)

        if instructor_id:
            courses = courses.filter(instructor_id=instructor_id)

        if min_price:
            courses = courses.filter(price__gte=min_price)

        if max_price:
            courses = courses.filter(price__lte=max_price)

        if is_featured:
            courses = courses.filter(is_featured=is_featured)

        if language:
            courses = courses.filter(language=language)

        if search:
            courses = courses.filter(title__icontains=search)

        if ordering:
            courses = courses.order_by(ordering)
        else:
            courses = courses.order_by('-price')

        return courses

    def get(self, request):
        courses = self.get_object(request)
        serializer = self.serializer_class(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDetailPutPatchDeleteAPIView(APIView):
    serializer_class = CourseDetailSerializer
    model = Course

    def get_object(self, request, pk):
        try:
            course = self.model.objects.get(pk=pk)
            return course
        except self.model.DoesNotExist:
            raise None

    def get(self, request, pk):
        course = self.get_object(request, pk)
        serializer = self.serializer_class(course, context={'request': request})
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        course = self.get_object(request, pk)
        if course is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if course.instructor.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(course, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        course = self.get_object(request, pk)
        if course is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if course.instructor.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(course, data=request.data, context={'request': request}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        course = self.get_object(request, pk)
        if course is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if course.instructor.user != request.user:
            return Response({"detail": "You are not allowed to delete this course."}, status=status.HTTP_403_FORBIDDEN)

        course.delete()
        return Response({"detail": "Course deleted successfully."}, status=status.HTTP_204_NO_CONTENT)












