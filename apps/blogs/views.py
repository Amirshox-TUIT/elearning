from django.contrib.auth import get_user_model, authenticate
from django.utils.text import slugify
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import CreateAPIView, get_object_or_404, RetrieveUpdateDestroyAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.blogs.models import Post, Category, Tag
from apps.blogs.serializers import RegisterSerializer, ProfileSerializer, PostListCreateSerializer, \
    PostRetrieveUpdateDestroySerializer

User = get_user_model()

class RegisterAPIView(CreateAPIView):
    serializer_class = RegisterSerializer
    queryset = User.objects.all()


class LoginAPIView(APIView):

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is None:
            return Response(
                {"detail": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = user.get_tokens_for_user()
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_id": user.id,
            "username": user.username
        }, status=status.HTTP_200_OK)

class LogoutAPIView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_205_RESET_CONTENT)
        except TokenError:
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProfileSerializer
    queryset = User.objects.all()
    lookup_field = 'username'
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get_object(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user != user:
                raise PermissionDenied("You cannot modify another user's profile.")
        print(f'Current user {self.request.user}')
        return user

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs, partial=True)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)



class PostListCreateAPIView(ListCreateAPIView):
    serializer_class = PostListCreateSerializer
    queryset = Post.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get_queryset(self):
        return Post.objects.filter(status='published')

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        category_id = self.request.data.pop('category_id')
        tags_id = self.request.data.pop('tags_id')

        if not category_id:
            raise ValidationError({'category_id': 'Category is required.'})
        if not tags_id:
            raise ValidationError({'tags_id': 'At least one tag is required.'})

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            raise ValidationError({'category_id': 'Invalid category ID.'})

        tags = Tag.objects.filter(id__in=tags_id)
        if not tags.exists():
            raise ValidationError({'tags_id': 'Invalid tags.'})


        title = self.request.data.get('title')
        content = self.request.data.get('content')
        author = self.request.user
        slug = slugify(title)
        excerpt = content[:30]
        post = serializer.save(
            category=category,
            tags=tags,
            slug=slug,
            excerpt=excerpt,
            author=author,
        )
        post.tags.set(*tags)


class PostRetrieveUpdateDestroyAPIView(RetrieveUpdateDestroyAPIView):
    serializer_class = PostRetrieveUpdateDestroySerializer
    queryset = Post.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get_object(self):
        post = get_object_or_404(Post, id=self.kwargs['pk'])
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            if self.request.user != post.author:
                raise PermissionDenied("You cannot modify another user's posts.")
        return post

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs, partial=True)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        post = self.get_object()
        category_id = request.data.pop('category_id', post.category.id)
        tags_id = request.data.pop('tags_id', None)
        if category_id:
            try:
                post.category = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                return Response({"detail": "Invalid category ID."}, status=status.HTTP_404_NOT_FOUND)

        if tags_id:
            tags = Tag.objects.filter(id__in=tags_id)
            if not tags.exists():
                return Response({"detail": "Invalid tags."}, status=status.HTTP_404_NOT_FOUND)
            post.tags.set(tags)

        title = request.data.get('title', post.title)
        post.slug = slugify(title)
        post.title = title

        content = request.data.get('content', post.content)
        post.excerpt = content[:30]
        post.content = content

        post.save()

        serializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)


