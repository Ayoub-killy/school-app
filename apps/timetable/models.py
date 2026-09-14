from django.db import models
from django.core.exceptions import ValidationError
from apps.accounts.models import User
from apps.sis.models import Stream, Subject


class Period(models.Model):
    """A fixed daily time slot, shared by every day Mon-Fri.
    Seeded once via a data migration / management command from the school's
    official timetable so times stay editable from admin without code changes.
    """
    class PeriodType(models.TextChoices):
        TEACHING = 'TEACHING', 'Teaching Period'
        BREAK = 'BREAK', 'Break'

    order = models.PositiveSmallIntegerField(
        unique=True, help_text="Sequence within the day, e.g. 1 = First Period"
    )
    label = models.CharField(max_length=50, help_text="e.g. 'First Period', 'Tea Break'")
    start_time = models.TimeField()
    end_time = models.TimeField()
    period_type = models.CharField(max_length=10, choices=PeriodType.choices)

    class Meta:
        ordering = ['order']

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("start_time must be before end_time.")

    def __str__(self):
        return f"{self.label} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')})"


class SubjectTeacherAssignment(models.Model):
    """Canonical answer to: 'who teaches Subject X for Stream Y?'
    This is set once by the Academic Master/HoS and feeds the generator.
    """
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='subject_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='stream_assignments')
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='timetable_assignments',
        limit_choices_to={'role': User.Role.TEACHER}
    )
    assigned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assignments_made'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('stream', 'subject')
        ordering = ['stream__school_class__order', 'stream__name', 'subject__name']

    def clean(self):
        # Guard rail: don't let a subject be assigned to a stream whose level it doesn't cover.
        if self.subject_id and self.stream_id:
            stream_level = self.stream.school_class.level
            if self.subject.levels != 'BOTH' and self.subject.levels != stream_level:
                raise ValidationError(
                    f"{self.subject} is not offered at {self.stream.school_class.get_level_display()}."
                )

    def __str__(self):
        return f"{self.subject} @ {self.stream} -> {self.teacher.get_full_name() or self.teacher.username}"


class Timetable(models.Model):
    """One generation batch of the whole-school timetable."""
    generated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='timetables_generated'
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        status = "ACTIVE" if self.is_active else "archived"
        return f"Timetable #{self.pk} ({status}) - {self.generated_at:%Y-%m-%d %H:%M}"


class TimetableEntry(models.Model):
    class Day(models.TextChoices):
        MONDAY = 'MON', 'Monday'
        TUESDAY = 'TUE', 'Tuesday'
        WEDNESDAY = 'WED', 'Wednesday'
        THURSDAY = 'THU', 'Thursday'
        FRIDAY = 'FRI', 'Friday'

    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name='entries')
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='timetable_entries')
    day = models.CharField(max_length=3, choices=Day.choices)
    period = models.ForeignKey(
        Period, on_delete=models.CASCADE, related_name='timetable_entries',
        limit_choices_to={'period_type': Period.PeriodType.TEACHING}
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable_entries')
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='timetable_entries',
        limit_choices_to={'role': User.Role.TEACHER}
    )

    class Meta:
        ordering = ['day', 'period__order']
        constraints = [
            # A stream can't have two subjects in the same slot on the same day.
            models.UniqueConstraint(
                fields=['timetable', 'stream', 'day', 'period'],
                name='unique_stream_slot_per_timetable'
            ),
            # A teacher can't be in two places in the same slot on the same day.
            models.UniqueConstraint(
                fields=['timetable', 'teacher', 'day', 'period'],
                name='unique_teacher_slot_per_timetable'
            ),
        ]

    def __str__(self):
        return f"{self.stream} | {self.get_day_display()} {self.period.label}: {self.subject} ({self.teacher})"
