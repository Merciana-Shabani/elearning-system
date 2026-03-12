from rest_framework import serializers
from .models import Course, CourseCategory, CourseSection, CourseModule


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ['id', 'name', 'description', 'parent', 'visible', 'course_count']


class CourseSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    teacher_name = serializers.ReadOnlyField(source='teacher.full_name')
    enrolled_count = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = [
            'id', 'fullname', 'shortname', 'idnumber', 'summary', 'image',
            'category', 'category_name', 'teacher', 'teacher_name',
            'format', 'enrollment_type', 'visible', 'startdate', 'enddate',
            'enrolled_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'enrolled_count']


class CourseSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseSection
        fields = ['id', 'course', 'section', 'name', 'summary', 'visible', 'sortorder']
