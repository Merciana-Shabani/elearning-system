from rest_framework import generics, permissions
from .models import Course, CourseCategory
from .serializers import CourseSerializer, CourseCategorySerializer


class CourseListAPIView(generics.ListCreateAPIView):
    queryset = Course.objects.filter(visible=True).select_related('category', 'teacher')
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CourseDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class CourseCategoryListAPIView(generics.ListAPIView):
    queryset = CourseCategory.objects.filter(visible=True)
    serializer_class = CourseCategorySerializer
    permission_classes = [permissions.AllowAny]
