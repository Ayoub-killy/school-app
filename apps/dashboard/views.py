from django.shortcuts import redirect
from apps.accounts.views import StyledAuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import render
from apps.accounts.models import User
from apps.sis.models import Student, Staff, Stream, SchoolClass
from apps.library.models import Book, BookCopy, LibraryMember, Loan

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    form = StyledAuthenticationForm()

    from apps.sis.models import Student, Staff, SchoolClass
    from apps.library.models import Book

    context = {
        'form': form,
        'stat_students': Student.objects.filter(status='ACTIVE').count(),
        'stat_staff': Staff.objects.filter(is_active=True).count(),
        'stat_classes': SchoolClass.objects.count(),
        'stat_books': Book.objects.count(),
    }
    return render(request, 'dashboard/landing.html', context)

@login_required
def home(request):
    active_role = request.session.get('active_role', request.user.role)

    if active_role == User.Role.DEPARTMENT_STAFF:
        from apps.resources.dept_views import department_dashboard
        return department_dashboard(request)

    context = {}
    role = active_role

    if role in (User.Role.HEAD_OF_SCHOOL, User.Role.ADMIN):
        from apps.accounts.models import StaffInvitation
        from apps.resources.models import Transaction

        context['total_students'] = Student.objects.filter(status='ACTIVE').count()
        context['total_staff'] = Staff.objects.filter(is_active=True).count()
        context['total_classes'] = SchoolClass.objects.count()
        context['total_books'] = Book.objects.count()
        context['pending_invitations'] = StaffInvitation.objects.filter(is_used=False).count()

        open_loans = Loan.objects.filter(returned_date__isnull=True)
        context['overdue_loans'] = sum(1 for loan in open_loans if loan.is_overdue())

        transactions = Transaction.objects.select_related('category').all()
        income = sum(t.amount for t in transactions if t.category.type == 'INCOME')
        expense = sum(t.amount for t in transactions if t.category.type == 'EXPENSE')
        context['balance'] = income - expense

    elif role == User.Role.TEACHER:
        context['subjects'] = request.user.subjects_taught.all()
        context['streams_managed'] = SchoolClass.objects.filter(class_teacher=request.user)

    elif role == User.Role.STUDENT:
        context['student_profile'] = getattr(request.user, 'student_profile', None)
    elif role == User.Role.ACADEMIC_MASTER:
        from apps.sis.models import Department
        context['total_students'] = Student.objects.filter(status='ACTIVE').count()
        context['o_level_count'] = Student.objects.filter(
            status='ACTIVE', stream__school_class__level='O_LEVEL'
        ).count()
        context['a_level_count'] = Student.objects.filter(
            status='ACTIVE', stream__school_class__level='A_LEVEL'
        ).count()
        context['total_classes'] = SchoolClass.objects.count()
        context['total_streams'] = Stream.objects.count()
        context['total_departments'] = Department.objects.count()
        context['classes_without_teacher'] = SchoolClass.objects.filter(class_teacher__isnull=True).count()
        context['class_breakdown'] = SchoolClass.objects.annotate(
            student_count=models.Count(
                'streams__students',
                filter=models.Q(streams__students__status__in=['ACTIVE', 'SUSPENDED', 'TRANSFERRED'])
            )
        ).order_by('order')

    elif role == User.Role.ACCOUNTANT:
        from apps.resources.models import Transaction, Invoice, InventoryItem

        transactions = Transaction.objects.select_related('category').all()
        context['total_income'] = sum(t.amount for t in transactions if t.category.type == 'INCOME')
        context['total_expense'] = sum(t.amount for t in transactions if t.category.type == 'EXPENSE')
        context['balance'] = context['total_income'] - context['total_expense']

        invoices = Invoice.objects.all()
        context['total_invoices'] = invoices.count()
        context['unpaid_invoices'] = [i for i in invoices if i.status() != 'PAID']
        context['total_outstanding'] = sum(i.balance() for i in invoices)

        items = InventoryItem.objects.all()
        context['low_stock_items'] = [i for i in items if i.is_low_stock()]
        context['total_items'] = items.count()

        context['recent_transactions'] = transactions.order_by('-date')[:5]

    elif role == User.Role.LIBRARIAN:
        active_loans = Loan.objects.filter(returned_date__isnull=True)
        context['total_books'] = Book.objects.count()
        context['total_copies'] = BookCopy.objects.count()
        context['available_copies'] = BookCopy.objects.filter(status='AVAILABLE').count()
        context['total_members'] = LibraryMember.objects.filter(is_active=True).count()
        context['active_loans_count'] = active_loans.count()
        context['overdue_loans'] = [loan for loan in active_loans if loan.is_overdue()]
        context['recent_loans'] = active_loans.select_related('book_copy__book', 'member')[:5]

    return render(request, 'dashboard/home.html', context)
from apps.core.decorators import role_required

HOS_ADMIN = ('HEAD_OF_SCHOOL', 'ADMIN')


@role_required(*HOS_ADMIN)
def academic_hub(request):
    return render(request, 'dashboard/academic_hub.html')


@role_required(*HOS_ADMIN)
def library_hub(request):
    from apps.library.models import Book, BookCopy, LibraryMember, Loan
    active_loans = Loan.objects.filter(returned_date__isnull=True)
    context = {
        'total_books': Book.objects.count(),
        'total_copies': BookCopy.objects.count(),
        'available_copies': BookCopy.objects.filter(status='AVAILABLE').count(),
        'total_members': LibraryMember.objects.filter(is_active=True).count(),
        'active_loans_count': active_loans.count(),
        'overdue_count': len([l for l in active_loans if l.is_overdue()]),
    }
    return render(request, 'dashboard/library_hub.html', context)


@role_required(*HOS_ADMIN)
def staff_hub(request):
    from apps.sis.models import Staff, Department
    context = {
        'total_staff': Staff.objects.filter(is_active=True).count(),
        'total_departments': Department.objects.count(),
        'departments_without_head': Department.objects.filter(head__isnull=True).count(),
    }
    return render(request, 'dashboard/staff_hub.html', context)


@role_required(*HOS_ADMIN)
def resources_hub(request):
    from apps.resources.models import Transaction, Invoice, InventoryItem
    transactions = Transaction.objects.select_related('category').all()
    invoices = Invoice.objects.all()
    items = InventoryItem.objects.all()
    context = {
        'total_income': sum(t.amount for t in transactions if t.category.type == 'INCOME'),
        'total_expense': sum(t.amount for t in transactions if t.category.type == 'EXPENSE'),
        'total_outstanding': sum(i.balance() for i in invoices),
        'low_stock_count': len([i for i in items if i.is_low_stock()]),
        'total_items': items.count(),
    }
    return render(request, 'dashboard/resources_hub.html', context)