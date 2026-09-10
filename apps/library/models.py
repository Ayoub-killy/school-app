from django.db import models
from django.utils import timezone
from apps.accounts.models import User
from apps.sis.models import Student, Staff


class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Book Categories'

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=20, blank=True, unique=True, null=True)
    publisher = models.CharField(max_length=150, blank=True)
    year_published = models.PositiveIntegerField(null=True, blank=True)
    category = models.ForeignKey(
        BookCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='books'
    )

    class Meta:
        ordering = ['title']

    def total_copies(self):
        return self.copies.count()

    def available_copies(self):
        return self.copies.filter(status='AVAILABLE').count()

    def __str__(self):
        return self.title


class BookCopy(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        BORROWED = 'BORROWED', 'Borrowed'
        LOST = 'LOST', 'Lost'
        DAMAGED = 'DAMAGED', 'Damaged'

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
    copy_number = models.CharField(max_length=20, help_text="e.g. Copy 1, Copy 2")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)

    class Meta:
        unique_together = ('book', 'copy_number')
        ordering = ['book__title', 'copy_number']
        verbose_name_plural = 'Book Copies'

    def __str__(self):
        return f"{self.book.title} - {self.copy_number}"


class LibraryMember(models.Model):
    class MemberType(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        STAFF = 'STAFF', 'Staff'
        EXTERNAL = 'EXTERNAL', 'External'

    member_type = models.CharField(max_length=10, choices=MemberType.choices)

    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, null=True, blank=True, related_name='library_member'
    )
    staff = models.OneToOneField(
        Staff, on_delete=models.CASCADE, null=True, blank=True, related_name='library_member'
    )

    # Only used when member_type = EXTERNAL
    external_full_name = models.CharField(max_length=150, blank=True)
    external_phone = models.CharField(max_length=20, blank=True)
    external_relationship = models.CharField(
        max_length=100, blank=True,
        help_text="e.g. Parent of [student name], Alumni, Community member"
    )

    date_joined = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date_joined']

    def clean(self):
        from django.core.exceptions import ValidationError
        filled = sum([
            self.member_type == self.MemberType.STUDENT and bool(self.student),
            self.member_type == self.MemberType.STAFF and bool(self.staff),
            self.member_type == self.MemberType.EXTERNAL and bool(self.external_full_name),
        ])
        if self.member_type == self.MemberType.STUDENT and not self.student:
            raise ValidationError("Select a Student when member type is Student.")
        if self.member_type == self.MemberType.STAFF and not self.staff:
            raise ValidationError("Select a Staff member when member type is Staff.")
        if self.member_type == self.MemberType.EXTERNAL and not self.external_full_name:
            raise ValidationError("Full name is required for external members.")
        if filled != 1:
            raise ValidationError("Member must be linked to exactly one identity: Student, Staff, or External details.")

    def __str__(self):
        if self.member_type == self.MemberType.STUDENT and self.student:
            return f"{self.student} (Student)"
        if self.member_type == self.MemberType.STAFF and self.staff:
            return f"{self.staff} (Staff)"
        return f"{self.external_full_name} (External)"


class Loan(models.Model):
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='loans')
    member = models.ForeignKey(LibraryMember, on_delete=models.CASCADE, related_name='loans')
    borrowed_date = models.DateField()
    due_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    issued_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='loans_issued'
    )

    class Meta:
        ordering = ['-borrowed_date']

    def is_overdue(self):
        if self.returned_date:
            return False
        return timezone.now().date() > self.due_date
class LibraryFine(models.Model):
    class Status(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PAID = 'PAID', 'Paid'
        WAIVED = 'WAIVED', 'Waived'

    member = models.ForeignKey(LibraryMember, on_delete=models.CASCADE, related_name='fines')
    # Linked to the loan so you know exactly WHICH book they lost/damaged
    loan = models.ForeignKey(Loan, on_delete=models.SET_NULL, null=True, blank=True, related_name='fines')
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=255, help_text="e.g., Lost Book, Damaged pages, Late return")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.UNPAID)
    date_issued = models.DateField(auto_now_add=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fines_issued')

    class Meta:
        ordering = ['-date_issued']

    def __str__(self):
        return f"{self.member} - {self.amount} ({self.get_status_display()})"
    