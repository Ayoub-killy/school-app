from django.contrib import admin
from .models import (
    AcademicYear, Semester, Term, Combination, SchoolClass, Stream,
    Department, Staff, Guardian, Student, StudentGuardianRelation, Subject,
    OLevelCategory,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'is_active']
    list_filter = ['is_active']


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'academic_year', 'start_date', 'end_date', 'is_active']
    list_filter = ['academic_year', 'is_active']

    
@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['name', 'semester', 'start_date', 'end_date', 'is_active']
    list_filter = ['semester', 'is_active']

@admin.register(Combination)
class CombinationAdmin(admin.ModelAdmin):
    list_display = ['code', 'full_name', 'category', 'added_by']
    list_filter = ['category']
    search_fields = ['code', 'full_name']


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'order', 'class_teacher']
    list_filter = ['level']
    ordering = ['order']


@admin.register(Stream)
class StreamAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'school_class', 'category']
    list_filter = ['school_class', 'category']

@admin.register(OLevelCategory)
class OLevelCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

    
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


class StudentGuardianInline(admin.TabularInline):
    model = StudentGuardianRelation
    extra = 1


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['staff_number', 'user', 'department', 'is_active']
    list_filter = ['department', 'is_active']
    search_fields = ['staff_number', 'user__first_name', 'user__last_name']


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'phone_number', 'email']
    search_fields = ['first_name', 'last_name', 'phone_number']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'first_name', 'last_name', 'stream', 'combination', 'status']
    list_filter = ['stream', 'combination', 'status']
    search_fields = ['admission_number', 'first_name', 'last_name']
    inlines = [StudentGuardianInline]

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'department', 'levels']
    list_filter = ['department', 'levels']
    search_fields = ['name', 'code']
    filter_horizontal = ['teachers']
