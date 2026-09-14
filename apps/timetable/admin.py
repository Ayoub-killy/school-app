from django.contrib import admin
from .models import Period, SubjectTeacherAssignment, Timetable, TimetableEntry


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('order', 'label', 'start_time', 'end_time', 'period_type')
    ordering = ('order',)


@admin.register(SubjectTeacherAssignment)
class SubjectTeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('stream', 'subject', 'teacher', 'assigned_by', 'created_at')
    list_filter = ('stream__school_class', 'subject')
    search_fields = ('stream__name', 'subject__name', 'teacher__username', 'teacher__first_name', 'teacher__last_name')
    raw_id_fields = ('stream',)
    autocomplete_fields = ('subject', 'teacher')


class TimetableEntryInline(admin.TabularInline):
    model = TimetableEntry
    extra = 0
    fields = ('stream', 'day', 'period', 'subject', 'teacher')
    raw_id_fields = ('stream',)
    autocomplete_fields = ('subject', 'teacher')

    
@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('id', 'generated_by', 'generated_at', 'is_active')
    list_filter = ('is_active',)
    inlines = [TimetableEntryInline]
