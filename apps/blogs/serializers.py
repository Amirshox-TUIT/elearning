from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from apps.blogs.models import AuthorProfile, Post, Category, Tag, PostImage, Comment, PostLike

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password_confirm')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists')
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('password_confirm')
        if password != confirm_password:
            raise serializers.ValidationError('Passwords must match')

        if len(password.strip()) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters')

        if password.isdigit() or password.isalpha():
            raise serializers.ValidationError('Password must contain at least one letter')

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        user.set_password(user.password)
        user.save()
        return user

class InlineProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorProfile
        fields = ('bio', 'avatar', 'website', 'twitter')

    def validate_bio(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Bio must be at least 10 characters')
        return value

    def validate_website(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError('Website must be at least 10 characters')
        return value


class ProfileSerializer(serializers.ModelSerializer):
    author = InlineProfileSerializer()
    posts = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'author')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists')
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')

        if value.strip() == '' or not value.endswith('@gmail.com'):
            raise serializers.ValidationError('Email must contain at least one letter')

        return value

    def validate_first_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError('First name must be at least 3 characters')
        return value

    def validate_last_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError('Last name must be at least 3 characters')
        return value

    def get_posts(self, user):
        return Post.objects.filter(author=user)


    def update(self, instance, validated_data):
        author_data = validated_data.pop('author', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if author_data:
            author = instance.author
            for attr, value in author_data.items():
                setattr(author, attr, value)
            author.save()

        return instance


class InlineCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'description')


class InlineTagsModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name',)


class InlineImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = "__all__"


class PostListCreateSerializer(serializers.ModelSerializer):
    tags = InlineTagsModelSerializer(many=True, read_only=True)
    category = InlineCategorySerializer(read_only=True)
    author = InlineProfileSerializer(read_only=True)
    images = InlineImagesSerializer(many=True, read_only=True)
    images_id = PrimaryKeyRelatedField(queryset=Post.objects.all(), write_only=True, many=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    tags_id = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, write_only=True)
    likes_count = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'excerpt', 'content', 'category',
                  'tags', 'author', 'status', 'category_id', 'tags_id']
        extra_kwargs = {
            'id': {'read_only': True},
            'slug': {'read_only': True},
            'excerpt': {'read_only': True},
        }

    def validate_title(self, value):
        if Post.objects.filter(title__iexact=value).exists():
            raise serializers.ValidationError("Title must be unique.")
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must contain at least 5 characters.")
        return value

    def validate_content(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Content must contain at least 20 characters.")
        return value

    def validate_tags_id(self, value):
        if not value:
            raise serializers.ValidationError("At least one tag is required.")
        return value

    def validate_category_id(self, value):
        if not value:
            raise serializers.ValidationError("Category is required.")
        return value

    def get_likes_count(self, post):
        return post.likes.count()

    def get_comments_count(self, post):
        return post.comments.count()


class PostRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    tags = InlineTagsModelSerializer(many=True, read_only=True)
    category = InlineCategorySerializer(read_only=True)
    author = InlineProfileSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField(read_only=True)
    comments_count = serializers.SerializerMethodField(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), write_only=True)
    tags_id = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, write_only=True)
    class Meta:
        model = Post
        fields = ('id', 'title', 'slug', 'excerpt', 'content', 'category', 'author', 'tags', 'category_id', 'tags_id')
        extra_kwargs = {
            'id': {'read_only': True},
            'slug': {'read_only': True},
            'excerpt': {'read_only': True},
        }

    def validate_title(self, value):
        if Post.objects.filter(title__iexact=value).exists():
            raise serializers.ValidationError("Title must be unique.")
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must contain at least 5 characters.")
        return value

    def validate_content(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Content must contain at least 20 characters.")
        return value

    def validate_tags_id(self, value):
        if not value:
            raise serializers.ValidationError("At least one tag is required.")
        return value

    def validate_category_id(self, value):
        if not value:
            raise serializers.ValidationError("Category is required.")
        return value

    def get_likes_count(self, post):
        return post.likes.count()

    def get_comments_count(self, post):
        return post.comments.count()


class InlineUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username',)


class InlineCommentSerializer(serializers.ModelSerializer):
    user = InlineUserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'content', 'user')


class CommentListCreateSerializer(serializers.ModelSerializer):
    user = InlineUserSerializer(read_only=True)
    parent = InlineCommentSerializer(read_only=True)
    parent_id = PrimaryKeyRelatedField(queryset=Comment.objects.all(), write_only=True, allow_null=True, required=False)

    class Meta:
        model = Comment
        exclude = ('is_public', )
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'post': {'read_only': True},
        }

    def validate_content(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Content must contain at least 5 characters.")
        return value

    def validate_parent_id(self, parent):
        if parent and not Comment.objects.filter(id=parent.id).exists():
            raise serializers.ValidationError("Parent must be exists.")
        return parent.id


class CommentRetrieveUpdateDestroySerializer(serializers.ModelSerializer):
    user = InlineUserSerializer(read_only=True)
    parent = InlineCommentSerializer(read_only=True)
    parent_id = PrimaryKeyRelatedField(queryset=Comment.objects.all(), write_only=True, allow_null=True, required=False)

    class Meta:
        model = Comment
        exclude = ('is_public',)
        extra_kwargs = {
            'id': {'read_only': True},
            'created_at': {'read_only': True},
            'post': {'read_only': True},
        }

    def validate_content(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Content must contain at least 5 characters.")
        return value

    def validate_parent_id(self, parent):
        if parent and not Comment.objects.filter(id=parent.id).exists():
            raise serializers.ValidationError("Parent must be exists.")
        return parent.id


class LikeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'user': {'read_only': True},
            'post': {'read_only': True},
        }

















