from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from apps.courses.models import Course
from apps.enrollment.models import Enrollment
from .models import Grade, GradeItem, GradeCategory


@login_required
def gradebook(request, course_pk):
    """Student's gradebook for a course."""
    course = get_object_or_404(Course, pk=course_pk)
    is_teacher = course.teacher == request.user or request.user.is_staff

    if not is_teacher:
        enrollment = get_object_or_404(
            Enrollment, user=request.user, course=course, status='active'
        )

    if is_teacher:
        # Show all students and their grades
        enrollments = Enrollment.objects.filter(
            course=course, status='active'
        ).select_related('user')
        grade_items = GradeItem.objects.filter(course=course).order_by('sortorder')

        # Build grade matrix
        grade_matrix = {}
        for enr in enrollments:
            user_grades = {}
            for item in grade_items:
                try:
                    grade = Grade.objects.get(item=item, user=enr.user)
                    user_grades[item.pk] = grade
                except Grade.DoesNotExist:
                    user_grades[item.pk] = None
            grade_matrix[enr.user.pk] = {
                'user': enr.user,
                'grades': user_grades,
            }

        return render(request, 'grades/gradebook_teacher.html', {
            'course': course,
            'grade_items': grade_items,
            'grade_matrix': grade_matrix,
        })
    else:
        # Student view: pass one row per grade item with item + grade (or None)
        grade_items = GradeItem.objects.filter(course=course).order_by('sortorder')
        grades_by_item = {
            g.item_id: g for g in Grade.objects.filter(
                user=request.user,
                item__course=course
            ).select_related('item')
        }
        grade_rows = [
            {'item': item, 'grade': grades_by_item.get(item.pk)}
            for item in grade_items
        ]

        return render(request, 'grades/gradebook_student.html', {
            'course': course,
            'grade_rows': grade_rows,
        })
