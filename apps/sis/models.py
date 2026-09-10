from django.db import models
from django.core.validators import RegexValidator
from apps.accounts.models import User


class AcademicYear(models.Model):
    year = models.CharField(max_length=9, unique=True, help_text="e.g. 2026")
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return self.year


class Semester(models.Model):
    class SemesterName(models.TextChoices):
        SEMESTER_1 = 'SEM1', 'Semester 1'
        SEMESTER_2 = 'SEM2', 'Semester 2'

    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='semesters'
    )
    name = models.CharField(max_length=4, choices=SemesterName.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('academic_year', 'name')
        ordering = ['academic_year', 'name']

    def label_for_level(self, level):
        """O-Level and A-Level number their semesters in reverse order."""
        if level == 'A_LEVEL':
            return 'Semester 2' if self.name == 'SEM1' else 'Semester 1'
        return self.get_name_display()

    def __str__(self):
        return f"{self.get_name_display()} - {self.academic_year.year}"

class Term(models.Model):
    class TermName(models.TextChoices):
        TERM1 = 'TERM1', 'Term 1'
        TERM2 = 'TERM2', 'Term 2'

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='terms')
    name = models.CharField(max_length=5, choices=TermName.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = ('semester', 'name')
        ordering = ['semester', 'name']

    def __str__(self):
        return f"{self.get_name_display()} - {self.semester}"

    
class Combination(models.Model):
    class Category(models.TextChoices):
        SCIENCE = 'SCIENCE', 'Science'
        ARTS = 'ARTS', 'Arts'
        ECONOMICS = 'ECONOMICS', 'Economics'

    code = models.CharField(max_length=10, unique=True, help_text="e.g. PCB")
    full_name = models.CharField(
        max_length=100, blank=True,
        help_text="e.g. Physics, Chemistry, Biology"
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='combinations_added'
    )

    class Meta:
        ordering = ['category', 'code']

    def __str__(self):
        return f"{self.code} ({self.get_category_display()})"


class SchoolClass(models.Model):
    class Level(models.TextChoices):
        O_LEVEL = 'O_LEVEL', 'Ordinary Level'
        A_LEVEL = 'A_LEVEL', 'Advanced Level'

    name = models.CharField(max_length=20, unique=True, help_text="e.g. Form 1")
    level = models.CharField(max_length=10, choices=Level.choices)
    order = models.PositiveSmallIntegerField(
        help_text="Used for sorting, e.g. Form 1 = 1, Form 2 = 2 ... Form 6 = 6"
    )
    class_teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='classes_managed',
        limit_choices_to={'role': User.Role.TEACHER}
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class OLevelCategory(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Science, Arts, ICT, Amali")

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'O-Level Categories'

    def __str__(self):
        return self.name


class Stream(models.Model):
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name='streams'
    )
    name = models.CharField(
        max_length=20,
        help_text="e.g. 'A' / 'B' for O-Level, or leave blank for A-Level (uses combination name)"
    )
    combination = models.ForeignKey(
        Combination, on_delete=models.PROTECT, null=True, blank=True,
        related_name='streams',
        help_text="Only set this for A-Level streams"
    )
    category = models.CharField(
        max_length=20,
        choices=Combination.Category.choices,
        blank=True,
        help_text="Only set this for A-Level streams (Science/Arts/Economics)"
    )
    combination = models.ForeignKey(
        Combination, on_delete=models.PROTECT, null=True, blank=True,
        related_name='streams',
        help_text="Only set this for A-Level streams"
    )
    category = models.CharField(
        max_length=20,
        choices=Combination.Category.choices,
        blank=True,
        help_text="Only set this for A-Level streams (Science/Arts/Economics)"
    )
    olevel_categories = models.ManyToManyField(
        OLevelCategory, blank=True, related_name='streams',
        help_text="Only for O-Level streams - check all categories this stream covers"
    )
    class Meta:
        unique_together = ('school_class', 'name')
        ordering = ['school_class__order', 'name']

    def __str__(self):
        if self.combination:
            return f"{self.school_class.name} {self.combination.code}"
        return f"{self.school_class.name} {self.name}"


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        'Staff', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='departments_headed'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Staff(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='staff_profile'
    )
    staff_number = models.CharField(max_length=20, unique=True, editable=False)
    photo = models.ImageField(upload_to='staff_photos/', null=True, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='staff_members'
    )
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1, choices=[('M', 'Male'), ('F', 'Female')], blank=True
    )
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['user__first_name']

    def save(self, *args, **kwargs):
        if not self.staff_number:
            last = Staff.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.staff_number = f"STF-{next_id:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.staff_number})"


class Guardian(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='guardian_profile'
    )
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        full_name = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))
        return full_name


class Student(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        TRANSFERRED = 'TRANSFERRED', 'Transferred'
        GRADUATED = 'GRADUATED', 'Graduated'

    user = models.OneToOneField(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='student_profile'
    )
    admission_number = models.CharField(max_length=20, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1, choices=[('M', 'Male'), ('F', 'Female')], blank=True
    )
    stream = models.ForeignKey(
        Stream, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='students'
    )
    combination = models.ForeignKey(
        Combination, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='students'
    )
    guardians = models.ManyToManyField(
        Guardian, through='StudentGuardianRelation', related_name='students'
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    date_admitted = models.DateField(auto_now_add=True)
    leaving_year = models.PositiveIntegerField(null=True, blank=True)
    leaving_class = models.CharField(max_length=20, blank=True, help_text="e.g. 'Form 4' or 'Form 6', set automatically when archived")

    class Meta:
        ordering = ['last_name', 'first_name']

    def save(self, *args, **kwargs):
        if not self.admission_number:
            last = Student.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.admission_number = f"STU-{next_id:05d}"
        super().save(*args, **kwargs)

    def __str__(self):
        full_name = " ".join(filter(None, [self.first_name, self.middle_name, self.last_name]))
        return f"{full_name} ({self.admission_number})"

class StudentGuardianRelation(models.Model):
    class Relationship(models.TextChoices):
        MOTHER = 'MOTHER', 'Mother'
        FATHER = 'FATHER', 'Father'
        GUARDIAN = 'GUARDIAN', 'Guardian'
        OTHER = 'OTHER', 'Other'

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE)
    relationship = models.CharField(max_length=20, choices=Relationship.choices)
    is_primary_contact = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'guardian')

    def __str__(self):
        return f"{self.guardian} - {self.get_relationship_display()} of {self.student}"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(
        max_length=10,
        unique=True,
        validators=[RegexValidator(r'^\d+$', message="Subject code must contain numbers only.")],
        help_text="e.g. 131 for Biology (numeric subject code)"
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='subjects'
    )
    levels = models.CharField(
        max_length=20,
        choices=[
            ('O_LEVEL', 'Ordinary Level'),
            ('A_LEVEL', 'Advanced Level'),
            ('BOTH', 'Both Levels'),
        ],
        default='BOTH'
    )
    teachers = models.ManyToManyField(
        User, blank=True, related_name='subjects_taught',
        limit_choices_to={'role': User.Role.TEACHER}
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"

class TeachingScheduleEntry(models.Model):
    class Day(models.TextChoices):
        MONDAY = 'MON', 'Monday'
        TUESDAY = 'TUE', 'Tuesday'
        WEDNESDAY = 'WED', 'Wednesday'
        THURSDAY = 'THU', 'Thursday'
        FRIDAY = 'FRI', 'Friday'
        SATURDAY = 'SAT', 'Saturday'

    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='schedule_entries',
        limit_choices_to={'role': User.Role.TEACHER}
    )
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='schedule_entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='schedule_entries')
    day = models.CharField(max_length=3, choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.get_day_display()} {self.start_time}-{self.end_time}: {self.subject} ({self.stream})"


class LessonPlan(models.Model):
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='lesson_plans',
        limit_choices_to={'role': User.Role.TEACHER}
    )
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name='lesson_plans')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lesson_plans')
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def total_subtopics(self):
        return SubTopic.objects.filter(topic__lesson_plan=self).count()

    def taught_subtopics(self):
        return SubTopic.objects.filter(topic__lesson_plan=self, is_taught=True).count()

    def progress_percent(self):
        total = self.total_subtopics()
        if total == 0:
            return 0
        return round((self.taught_subtopics() / total) * 100)

    def __str__(self):
        return f"{self.subject} - {self.stream} ({self.start_date} to {self.end_date})"


class Topic(models.Model):
    lesson_plan = models.ForeignKey(LessonPlan, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def total_subtopics(self):
        return self.subtopics.count()

    def taught_subtopics(self):
        return self.subtopics.filter(is_taught=True).count()

    def progress_percent(self):
        total = self.total_subtopics()
        if total == 0:
            return 0
        return round((self.taught_subtopics() / total) * 100)

    def __str__(self):
        return self.title


class SubTopic(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='subtopics')
    title = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)
    is_taught = models.BooleanField(default=False)
    date_taught = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title

        