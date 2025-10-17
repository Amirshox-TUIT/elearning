from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination

from apps.reviews.models import CourseReview


class CourseReviewListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseReview
        fields = ['rating', 'title', 'comment']

    def validate_title(self, title):
        if len(title) < 5:
            raise serializers.ValidationError('Title must be at least 5 characters')
        return title

    def validate_comment(self, comment):
        if len(comment) < 20:
            raise serializers.ValidationError('Comment must be at least 5 characters')
        return comment

    def validate_rating(self, rating):
        if rating < 0 or rating > 5:
            raise serializers.ValidationError('Rating must be between 0 and 5')
        return rating


class ReviewRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseReview
        fields = ['rating', 'title', 'comment']

    def validate_title(self, title):
        if len(title) < 5:
            raise serializers.ValidationError('Title must be at least 5 characters')
        return title

    def validate_comment(self, comment):
        if len(comment) < 20:
            raise serializers.ValidationError('Comment must be at least 5 characters')
        return comment

    def validate_rating(self, rating):
        if rating < 0 or rating > 5:
            raise serializers.ValidationError('Rating must be between 0 and 5')
        return rating


class PagePaginationSerializer(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page'
    max_page_size = 100

