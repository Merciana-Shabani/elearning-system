from django.contrib import admin
from .models import GradeCategory, GradeItem, Grade


@admin.register(GradeCategory)
class GradeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'aggregation', 'hidden']
    list_filter = ['aggregation', 'course']
    search_fields = ['name', 'course__fullname']


@admin.register(GradeItem)
class GradeItemAdmin(admin.ModelAdmin):
    list_display = ['item_name', 'course', 'item_type', 'grade_max', 'grade_pass', 'sortorder']
    list_filter = ['item_type', 'course']
    search_fields = ['item_name', 'course__fullname']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['user', 'item', 'finalgrade', 'overridden', 'updated_at']
    list_filter = ['item__course']
    search_fields = ['user__email', 'item__item_name']
    raw_id_fields = ['user', 'item']
