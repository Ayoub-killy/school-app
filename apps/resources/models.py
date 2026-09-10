from django.db import models
from apps.accounts.models import User
from apps.sis.models import Student, Staff


class TransactionCategory(models.Model):
    class Type(models.TextChoices):
        INCOME = 'INCOME', 'Income'
        EXPENSE = 'EXPENSE', 'Expense'

    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=Type.choices)

    class Meta:
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    category = models.ForeignKey(
        TransactionCategory, on_delete=models.PROTECT, related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions_recorded'
    )
    student = models.ForeignKey(
        Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions'
    )
    staff = models.ForeignKey(
        Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions'
    )
    department = models.ForeignKey(
        'sis.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions'
    )
    receipt = models.ImageField(upload_to='transaction_receipts/', null=True, blank=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.category.name} - {self.amount} ({self.date})"
from apps.sis.models import SchoolClass, AcademicYear, Semester


class FeeStructure(models.Model):
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name='fee_structures'
    )
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name='fee_structures'
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name='fee_structures'
    )
    term = models.ForeignKey(
        'sis.Term', on_delete=models.CASCADE, null=True, blank=True, related_name='fee_structures',
        help_text="Leave blank for a full-semester fee, or select a Term for a single installment"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('school_class', 'academic_year', 'semester', 'term')
        ordering = ['-academic_year', 'semester', 'school_class__order']

    def __str__(self):
        period = self.term if self.term else self.semester
        return f"{self.school_class.name} - {period} {self.academic_year.year} ({self.amount})"

class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Partially Paid'
        PAID = 'PAID', 'Paid'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='invoices')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.PROTECT, related_name='invoices')
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'fee_structure')
        ordering = ['-created_at']

    def total_paid(self):
        return sum(p.amount_paid for p in self.payments.all())

    def balance(self):
        return self.amount_due - self.total_paid()

    def status(self):
        paid = self.total_paid()
        if paid <= 0:
            return self.Status.UNPAID
        elif paid < self.amount_due:
            return self.Status.PARTIALLY_PAID
        return self.Status.PAID

    def get_status_display(self):
        return dict(self.Status.choices)[self.status()]

    def __str__(self):
        return f"{self.student} - {self.fee_structure}"


class Payment(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateField()
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_recorded'
    )
    transaction = models.OneToOneField(
        Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment'
    )

    class Meta:
        ordering = ['-date_paid']

    def __str__(self):
        return f"{self.invoice.student} paid {self.amount_paid} on {self.date_paid}"
class ItemCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Item Categories'

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    name = models.CharField(max_length=150)
    category = models.ForeignKey(
        ItemCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items'
    )
    unit = models.CharField(max_length=30, help_text="e.g. pieces, reams, litres, kg")
    reorder_level = models.PositiveIntegerField(
        default=0, help_text="Alert when stock falls to or below this quantity"
    )

    class Meta:
        ordering = ['name']

    def current_stock(self):
        total_in = sum(m.quantity for m in self.movements.filter(movement_type='IN'))
        total_out = sum(m.quantity for m in self.movements.filter(movement_type='OUT'))
        return total_in - total_out

    def is_low_stock(self):
        return self.current_stock() <= self.reorder_level

    def __str__(self):
        return f"{self.name} ({self.unit})"


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = 'IN', 'Stock In'
        OUT = 'OUT', 'Stock Out'

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=3, choices=MovementType.choices)
    quantity = models.PositiveIntegerField()
    date = models.DateField()
    reason = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements_recorded'
    )

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} ({self.quantity})"

class DepartmentDemand(models.Model):
    department = models.ForeignKey('sis.Department', on_delete=models.CASCADE, related_name='demands')
    description = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    date_needed = models.DateField()
    time_needed = models.TimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_needed']

    def __str__(self):
        return f"{self.description} x{self.quantity} - {self.department}"


class DepartmentInventoryRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        MISSING = 'MISSING', 'Missing'
        USED = 'USED', 'Used'

    department = models.ForeignKey('sis.Department', on_delete=models.CASCADE, related_name='inventory_records')
    item_name = models.CharField(max_length=150)
    status = models.CharField(max_length=10, choices=Status.choices)
    quantity = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=255, blank=True)
    date = models.DateField()
    time = models.TimeField()
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.item_name} ({self.get_status_display()}) - {self.department}"


class DepartmentReport(models.Model):
    department = models.ForeignKey('sis.Department', on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to='department_reports/')
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_head = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
