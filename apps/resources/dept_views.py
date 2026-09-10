from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import os

from .forms import DepartmentDemandForm, DepartmentInventoryForm, DepartmentTransactionForm
from .models import (
    DepartmentDemand, DepartmentInventoryRecord, DepartmentReport,
    Transaction, TransactionCategory,
)


def _get_my_department(request):
    """A Department Staff user must be linked as Staff, and that Staff's department is theirs to manage."""
    staff_profile = getattr(request.user, 'staff_profile', None)
    if not staff_profile or not staff_profile.department:
        raise PermissionDenied("Your account isn't linked to a department yet. Contact the administrator.")
    return staff_profile.department


@login_required
def department_dashboard(request):
    active_role = request.session.get('active_role', request.user.role)
    if active_role != 'DEPARTMENT_STAFF':
        raise PermissionDenied
    department = _get_my_department(request)

    demands = DepartmentDemand.objects.filter(department=department)[:5]
    inventory = DepartmentInventoryRecord.objects.filter(department=department)[:5]
    transactions = Transaction.objects.filter(department=department)
    total_income = sum(t.amount for t in transactions if t.category.type == 'INCOME')
    total_expense = sum(t.amount for t in transactions if t.category.type == 'EXPENSE')
    reports = DepartmentReport.objects.filter(department=department)[:5]

    return render(request, 'resources/department_dashboard.html', {
        'department': department,
        'demands': demands,
        'inventory': inventory,
        'total_income': total_income,
        'total_expense': total_expense,
        'reports': reports,
    })


@login_required
def demand_list(request):
    department = _get_my_department(request)
    demands = DepartmentDemand.objects.filter(department=department)

    if request.method == 'POST':
        form = DepartmentTransactionForm(request.POST, request.FILES)
        if form.is_valid():
            demand = form.save(commit=False)
            demand.department = department
            demand.recorded_by = request.user
            demand.save()
            messages.success(request, 'Demand recorded successfully.')
            return redirect('resources:demand_list')
    else:
        form = DepartmentDemandForm()

    return render(request, 'resources/demand_list.html', {'demands': demands, 'form': form, 'department': department})


@login_required
def demand_delete(request, pk):
    department = _get_my_department(request)
    demand = get_object_or_404(DepartmentDemand, pk=pk, department=department)
    if request.method == 'POST':
        demand.delete()
        messages.success(request, 'Demand deleted.')
    return redirect('resources:demand_list')


@login_required
def department_inventory_list(request):
    department = _get_my_department(request)
    records = DepartmentInventoryRecord.objects.filter(department=department)

    if request.method == 'POST':
        form = DepartmentInventoryForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.department = department
            record.recorded_by = request.user
            record.save()
            messages.success(request, 'Inventory record saved successfully.')
            return redirect('resources:department_inventory_list')
    else:
        form = DepartmentInventoryForm(initial={'date': timezone.now().date(), 'time': timezone.now().time()})

    return render(request, 'resources/department_inventory_list.html', {
        'records': records, 'form': form, 'department': department,
    })


@login_required
def department_transaction_list(request):
    department = _get_my_department(request)
    transactions = Transaction.objects.filter(department=department).select_related('category')
    total_income = sum(t.amount for t in transactions if t.category.type == 'INCOME')
    total_expense = sum(t.amount for t in transactions if t.category.type == 'EXPENSE')

    if request.method == 'POST':
        form = DepartmentTransactionForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.department = department
            t.recorded_by = request.user
            t.save()
            messages.success(request, 'Transaction recorded successfully.')
            return redirect('resources:department_transaction_list')
    else:
        form = DepartmentTransactionForm()

    return render(request, 'resources/department_transaction_list.html', {
        'transactions': transactions, 'form': form, 'department': department,
        'total_income': total_income, 'total_expense': total_expense,
    })


@login_required
def department_report_generate(request):
    department = _get_my_department(request)

    if request.method == 'POST':
        send_to_head = request.POST.get('send_to_head') == '1'

        demands = DepartmentDemand.objects.filter(department=department)
        inventory = DepartmentInventoryRecord.objects.filter(department=department)
        transactions = Transaction.objects.filter(department=department).select_related('category')
        total_income = sum(t.amount for t in transactions if t.category.type == 'INCOME')
        total_expense = sum(t.amount for t in transactions if t.category.type == 'EXPENSE')

        filename = f"dept_report_{department.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join('media', 'department_reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        y = height - 2 * cm

        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, y, f"REPORT FROM {department.name.upper()}")
        y -= 1 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        y -= 1.2 * cm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Financial Summary")
        y -= 0.7 * cm
        c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, f"Total Income: {total_income}")
        y -= 0.5 * cm
        c.drawString(2 * cm, y, f"Total Expense: {total_expense}")
        y -= 1 * cm

        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Demands")
        y -= 0.7 * cm
        c.setFont("Helvetica", 9)
        for d in demands[:20]:
            c.drawString(2 * cm, y, f"- {d.description} x{d.quantity} (needed {d.date_needed})")
            y -= 0.45 * cm
            if y < 3 * cm:
                c.showPage()
                y = height - 2 * cm

        y -= 0.5 * cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Inventory Records")
        y -= 0.7 * cm
        c.setFont("Helvetica", 9)
        for i in inventory[:20]:
            c.drawString(2 * cm, y, f"- {i.item_name}: {i.get_status_display()} x{i.quantity} ({i.date} {i.time})")
            y -= 0.45 * cm
            if y < 3 * cm:
                c.showPage()
                y = height - 2 * cm

        c.save()

        report = DepartmentReport.objects.create(
            department=department,
            title=f"REPORT FROM {department.name.upper()} - {timezone.now().strftime('%Y-%m-%d')}",
            pdf_file=f'department_reports/{filename}',
            generated_by=request.user,
            sent_to_head=send_to_head,
            sent_at=timezone.now() if send_to_head else None,
        )

        if send_to_head:
            messages.success(request, 'Report generated and sent to Head of School.')
        else:
            messages.success(request, 'Report generated successfully.')
        return redirect('resources:department_dashboard')

    return render(request, 'resources/department_report_confirm.html', {'department': department})


@login_required
def head_reports_list(request):
    if request.user.role not in ('HEAD_OF_SCHOOL', 'ADMIN'):
        raise PermissionDenied
    reports = DepartmentReport.objects.filter(sent_to_head=True).select_related('department', 'generated_by')
    return render(request, 'resources/head_reports_list.html', {'reports': reports})
