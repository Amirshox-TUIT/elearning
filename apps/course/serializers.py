from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from rest_framework import serializers
from apps.course.models import Category, Instructor, Course, Lesson, Section
from apps.reviews.models import CourseReview

User = get_user_model()

class InlineCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        exclude = ('parent', 'is_active')


class InlineUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


class InlineInstructorSerializer(serializers.ModelSerializer):
    user = InlineUserSerializer()
    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = Instructor
        fields = '__all__'

    def get_courses_count(self, obj):
        return obj.courses.count()


class CourseListCreateSerializer(serializers.ModelSerializer):
    category = InlineCategorySerializer(read_only=True)
    instructor = InlineInstructorSerializer(read_only=True)
    final_price = serializers.SerializerMethodField(read_only=True)
    total_lessons = serializers.SerializerMethodField(read_only=True)
    total_duration = serializers.SerializerMethodField(read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    average_rating = serializers.SerializerMethodField(read_only=True)
    reviews_count = serializers.SerializerMethodField(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        write_only=True,
        source='category',
    )
    instructor_id = serializers.PrimaryKeyRelatedField(
        queryset=Instructor.objects.all(),
        write_only=True,
        source='instructor',
    )

    class Meta:
        model = Course
        exclude = ['id', 'created_at', 'updated_at', 'is_featured']
        extra_kwargs = {
            'slug': {'read_only': True},
        }

    def get_final_price(self, obj):
        return Decimal(obj.price) * Decimal((1 - Decimal(obj.discount_percentage) / 100))

    def get_total_lessons(self, obj):
        return sum(section.lessons.count() for section in obj.sections.all())

    def get_total_duration(self, obj):
        return sum(
            lesson.duration_minutes
            for section in obj.sections.all()
            for lesson in section.lessons.all()
        )

    def get_students_count(self, obj):
        return obj.enrollments.count()

    def get_average_rating(self, obj):
        return sum(review.rating for review in obj.reviews.all()) / obj.reviews.count() \
            if obj.reviews.count() else 0

    def get_reviews_count(self, obj):
        return obj.reviews.count()

    def validate_title(self, title):
        if len(title) < 10:
            raise serializers.ValidationError('Title must be at least 10 characters')
        return title

    def validate_description(self, description):
        if len(description) < 50:
            raise serializers.ValidationError('Description must be at least 50 characters')
        return description

    def validate_price(self, price):
        if price <= Decimal(0):
            raise serializers.ValidationError('Price must be greater than 0')
        return price

    def validate_discount_percentage(self, discount_percentage):
        if not (0 <= discount_percentage <= 100):
            raise serializers.ValidationError('Discount percentage must be between 0 and 100')
        return discount_percentage

    def validate_duration_hours(self, duration_hours):
        if duration_hours <= 0:
            raise serializers.ValidationError('Duration hours must be greater than 0')
        return duration_hours

    def validate_instructor_id(self, instructor):
        if not instructor.is_verified:
            raise serializers.ValidationError('Instructor must be verified')
        return instructor

    def validate_category_id(self, category):
        if not category.is_active:
            raise serializers.ValidationError('Category must be active')
        return category

    def validate_level(self, level):
        if not any(level in Level for Level in Course.LEVEL_CHOICES):
            raise serializers.ValidationError('Level must be in {}'.format(Course.LEVEL_CHOICES))
        return level

    def validate_status(self, status):
        if not any(status in Status for Status in Course.LEVEL_CHOICES):
            raise serializers.ValidationError('Status must be in {}'.format(Course.STATUS_CHOICES))
        return status

    def validate_language(self, language):
        if language.strip() == '':
            raise serializers.ValidationError('Language must not be empty')
        return language

    def create(self, validated_data):
        title = validated_data.get('title')
        slug = slugify(title)
        counter = 1
        while Course.objects.filter(slug=slug).exists():
            slug = f"{slugify(title)}-{counter}"
            counter += 1
        validated_data['slug'] = slug
        return super().create(validated_data)


class InlineStudentSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('id', 'username', 'full_name')

    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'


class InlineLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'duration_minutes', 'order', 'is_preview')


class InlineSectionSerializer(serializers.ModelSerializer):
    lessons = InlineLessonSerializer(many=True)
    lessons_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    class Meta:
        model = Section
        fields = ('id', 'title', 'description', 'order', 'lessons', 'lessons_count', 'total_duration')

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_total_duration(self, obj):
        return sum(lesson.duration_minutes for lesson in obj.lessons.all())


class InlineReviewSerializer(serializers.ModelSerializer):
    student = InlineStudentSerializer()
    class Meta:
        model = CourseReview
        fields = ('id', 'student', 'rating', 'title', 'comment', 'created_at')



class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = InlineInstructorSerializer(read_only=True)
    instructor_id = serializers.PrimaryKeyRelatedField(
        queryset=Instructor.objects.all(),
        source='instructor',
        write_only=True
    )
    category = InlineCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    sections = InlineSectionSerializer(many=True, read_only=True)
    sections_id = serializers.PrimaryKeyRelatedField(
        source='sections',
        queryset=Section.objects.all(),
        write_only=True,
        many=True
    )
    reviews = InlineReviewSerializer(many=True, read_only=True)
    reviews_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseReview.objects.all(),
        source='reviews',
        write_only=True,
        many=True
    )
    final_price = serializers.SerializerMethodField(read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    total_sections = serializers.SerializerMethodField(read_only=True)
    total_lessons = serializers.SerializerMethodField(read_only=True)
    total_duration_minutes = serializers.SerializerMethodField(read_only=True)
    students_count = serializers.SerializerMethodField(read_only=True)
    reviews_count = serializers.SerializerMethodField(read_only=True)
    average_rating = serializers.SerializerMethodField(read_only=True)
    is_enrolled = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        fields = "__all__"
        extra_kwargs = {
            'id': {'read_only': True},
            'slug': {'read_only': True},
        }

    def get_final_price(self, obj):
        return Decimal(obj.price) * Decimal((1 - Decimal(obj.discount_percentage) / 100))

    def get_total_lessons(self, obj):
        return sum(section.lessons.count() for section in obj.sections.all())

    def get_total_duration_minutes(self, obj):
        return sum(
            lesson.duration_minutes
            for section in obj.sections.all()
            for lesson in section.lessons.all()
        )

    def get_students_count(self, obj):
        return obj.enrollments.count()

    def get_average_rating(self, obj):
        return sum(review.rating for review in obj.reviews.all()) / obj.reviews.count() \
            if obj.reviews.count() else 0

    def get_reviews_count(self, obj):
        return obj.reviews.count()

    def get_total_sections(self, obj):
        return obj.sections.count()

    def get_is_enrolled(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return obj.enrollments.filter(student=user).exists()

    def validate_title(self, title):
        if len(title) < 10:
            raise serializers.ValidationError('Title must be at least 10 characters')
        return title

    def validate_description(self, description):
        if len(description) < 50:
            raise serializers.ValidationError('Description must be at least 50 characters')
        return description

    def validate_price(self, price):
        if price <= Decimal(0):
            raise serializers.ValidationError('Price must be greater than 0')
        return price

    def validate_discount_percentage(self, discount_percentage):
        if not (0 <= discount_percentage <= 100):
            raise serializers.ValidationError('Discount percentage must be between 0 and 100')
        return discount_percentage

    def validate_duration_hours(self, duration_hours):
        if duration_hours <= 0:
            raise serializers.ValidationError('Duration hours must be greater than 0')
        return duration_hours

    def validate_status(self, status):
        if not any(status in Status for Status in Course.STATUS_CHOICES):
            raise serializers.ValidationError('Status must be one of these statuses')
        return status

    def update(self, instance, validated_data):
        title = validated_data.get('title', instance.title)
        if title != instance.title:
            slug = slugify(title)
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{slugify(title)}-{counter}"
                counter += 1
            validated_data['slug'] = slug
        return super().update(instance, validated_data)









