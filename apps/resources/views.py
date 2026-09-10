from django.contrib.auth.decorators import login_required
from apps.core.decorators import role_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .forms import (
    TransactionCategoryForm, TransactionForm, FeeStructureForm, PaymentForm,
    ItemCategoryForm, InventoryItemForm, StockMovementForm,
)
from .models import (
    TransactionCategory, Transaction, FeeStructure, Invoice, Payment,
    ItemCategory, InventoryItem, StockMovement,
)
from apps.sis.models import Student
import json
from datetime import date
from django.db.models import Sum, Q
from apps.sis.models import Department

RESOURCE_ROLES = ('ACCOUNTANT', 'HEAD_OF_SCHOOL', 'ADMIN')

@role_required(*RESOURCE_ROLES)
def category_list(request):
    categories = TransactionCategory.objects.all()
    return render(request, 'resources/category_list.html', {'categories': categories})


@role_required(*RESOURCE_ROLES)
def category_create(request):
    if request.method == 'POST':
        form = TransactionCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('resources:category_list')
    else:
        form = TransactionCategoryForm()
    return render(request, 'resources/category_form.html', {'form': form})


@role_required(*RESOURCE_ROLES)
def category_update(request, pk):
    category = get_object_or_404(TransactionCategory, pk=pk)
    if request.method == 'POST':
        form = TransactionCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('resources:category_list')
    else:
        form = TransactionCategoryForm(instance=category)
    return render(request, 'resources/category_form.html', {'form': form, 'category': category})


@role_required(*RESOURCE_ROLES)
def category_delete(request, pk):
    category = get_object_or_404(TransactionCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('resources:category_list')
    return render(request, 'resources/category_confirm_delete.html', {'category': category})


@role_required(*RESOURCE_ROLES)
def transaction_list(request):
    transactions = Transaction.objects.select_related('category', 'student', 'staff').all()
    total_income = sum(t.amount for t in transactions if t.category.type == 'INCOME')
    total_expense = sum(t.amount for t in transactions if t.category.type == 'EXPENSE')

    categories = TransactionCategory.objects.all()
    grouped = []
    for cat in categories:
        cat_transactions = [t for t in transactions if t.category_id == cat.id]
        if cat_transactions:
            grouped.append({
                'category': cat,
                'transactions': cat_transactions,
                'total': sum(t.amount for t in cat_transactions),
            })

    return render(request, 'resources/transaction_list.html', {
        'grouped': grouped,
        'total_income': total_income,
        'total_expense': total_expense,
        'balance': total_income - total_expense,
    })


@role_required(*RESOURCE_ROLES)
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.recorded_by = request.user
            transaction.save()
            messages.success(request, 'Transaction recorded successfully.')
            return redirect('resources:transaction_list')
    else:
        form = TransactionForm()
    return render(request, 'resources/transaction_form.html', {'form': form})


@role_required(*RESOURCE_ROLES)
def transaction_update(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully.')
            return redirect('resources:transaction_list')
    else:
        form = TransactionForm(instance=transaction)
    return render(request, 'resources/transaction_form.html', {'form': form, 'transaction': transaction})


@role_required(*RESOURCE_ROLES)
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully.')
        return redirect('resources:transaction_list')
    return render(request, 'resources/transaction_confirm_delete.html', {'transaction': transaction})
@role_required(*RESOURCE_ROLES)
def feestructure_list(request):
    fee_structures = FeeStructure.objects.select_related('school_class', 'academic_year', 'semester').all()
    return render(request, 'resources/feestructure_list.html', {'fee_structures': fee_structures})


@role_required(*RESOURCE_ROLES)
def feestructure_create(request):
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee structure created successfully.')
            return redirect('resources:feestructure_list')
    else:
        form = FeeStructureForm()
    return render(request, 'resources/feestructure_form.html', {'form': form})


@role_required(*RESOURCE_ROLES)
def feestructure_update(request, pk):
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee structure updated successfully.')
            return redirect('resources:feestructure_list')
    else:
        form = FeeStructureForm(instance=fee_structure)
    return render(request, 'resources/feestructure_form.html', {'form': form, 'fee_structure': fee_structure})


@role_required(*RESOURCE_ROLES)
def feestructure_delete(request, pk):
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        fee_structure.delete()
        messages.success(request, 'Fee structure deleted successfully.')
        return redirect('resources:feestructure_list')
    return render(request, 'resources/feestructure_confirm_delete.html', {'fee_structure': fee_structure})


@role_required(*RESOURCE_ROLES)
def generate_invoices(request, pk):
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    if request.method == 'POST':
        students = Student.objects.filter(
            status='ACTIVE', stream__school_class=fee_structure.school_class
        )
        due_date = fee_structure.term.end_date if fee_structure.term else fee_structure.semester.end_date
        created_count = 0
        for student in students:
            invoice, was_created = Invoice.objects.get_or_create(
                student=student,
                fee_structure=fee_structure,
                defaults={
                    'amount_due': fee_structure.amount,
                    'due_date': due_date,
                }
            )
            if was_created:
                created_count += 1
        messages.success(request, f'{created_count} invoice(s) generated successfully.')
        return redirect('resources:invoice_list')
    return render(request, 'resources/generate_invoices_confirm.html', {'fee_structure': fee_structure})

@role_required(*RESOURCE_ROLES)
def invoice_list(request):
    invoices = Invoice.objects.select_related('student', 'fee_structure').all()
    return render(request, 'resources/invoice_list.html', {'invoices': invoices})


@role_required(*RESOURCE_ROLES)
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    payments = invoice.payments.all()

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.recorded_by = request.user
            payment.save()

            fee_category, _ = TransactionCategory.objects.get_or_create(
                name='Tuition Fees', defaults={'type': 'INCOME'}
            )
            transaction = Transaction.objects.create(
                category=fee_category,
                amount=payment.amount_paid,
                date=payment.date_paid,
                description=f'Fee payment - {invoice}',
                recorded_by=request.user,
                student=invoice.student,
            )
            payment.transaction = transaction
            payment.save()

            messages.success(request, 'Payment recorded successfully.')
            return redirect('resources:invoice_detail', pk=invoice.pk)
    else:
        form = PaymentForm()

    return render(request, 'resources/invoice_detail.html', {
        'invoice': invoice,
        'payments': payments,
        'form': form,
    })
@role_required(*RESOURCE_ROLES)
def itemcategory_list(request):
    categories = ItemCategory.objects.all()
    return render(request, 'resources/itemcategory_list.html', {'categories': categories})


@role_required(*RESOURCE_ROLES)
def itemcategory_create(request):
    if request.method == 'POST':
        form = ItemCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item category created successfully.')
            return redirect('resources:itemcategory_list')
    else:
        form = ItemCategoryForm()
    return render(request, 'resources/itemcategory_form.html', {'form': form})


@role_required(*RESOURCE_ROLES)
def itemcategory_update(request, pk):
    category = get_object_or_404(ItemCategory, pk=pk)
    if request.method == 'POST':
        form = ItemCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item category updated successfully.')
            return redirect('resources:itemcategory_list')
    else:
        form = ItemCategoryForm(instance=category)
    return render(request, 'resources/itemcategory_form.html', {'form': form, 'category': category})


@role_required(*RESOURCE_ROLES)
def itemcategory_delete(request, pk):
    category = get_object_or_404(ItemCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Item category deleted successfully.')
        return redirect('resources:itemcategory_list')
    return render(request, 'resources/itemcategory_confirm_delete.html', {'category': category})


@role_required(*RESOURCE_ROLES)
def item_list(request):
    items = InventoryItem.objects.select_related('category').all()
    return render(request, 'resources/item_list.html', {'items': items})


@role_required(*RESOURCE_ROLES)
def item_create(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item created successfully.')
            return redirect('resources:item_list')
    else:
        form = InventoryItemForm()
    return render(request, 'resources/item_form.html', {'form': form})


@role_required(*RESOURCE_ROLES)
def item_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated successfully.')
            return redirect('resources:item_list')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'resources/item_form.html', {'form': form, 'item': item})


@role_required(*RESOURCE_ROLES)
def item_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully.')
        return redirect('resources:item_list')
    return render(request, 'resources/item_confirm_delete.html', {'item': item})


@role_required(*RESOURCE_ROLES)
def item_detail(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    movements = item.movements.all()

    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.item = item
            movement.recorded_by = request.user
            movement.save()
            messages.success(request, 'Stock movement recorded successfully.')
            return redirect('resources:item_detail', pk=item.pk)
    else:
        form = StockMovementForm()

    return render(request, 'resources/item_detail.html', {
        'item': item,
        'movements': movements,
        'form': form,
    })

@login_required
@role_required(*RESOURCE_ROLES)
def department_comparison(request):
    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    departments = Department.objects.all().order_by('name')
    labels = []
    income_data = []
    expense_data = []
    rows = []

    for dept in departments:
        qs = Transaction.objects.filter(department=dept, date__year=year, date__month=month)
        income = qs.filter(category__type='INCOME').aggregate(total=Sum('amount'))['total'] or 0
        expense = qs.filter(category__type='EXPENSE').aggregate(total=Sum('amount'))['total'] or 0
        net = income - expense

        labels.append(dept.name)
        income_data.append(float(income))
        expense_data.append(float(expense))
        rows.append({
            'department': dept.name,
            'income': income,
            'expense': expense,
            'net': net,
        })

    context = {
        'labels_json': json.dumps(labels),
        'income_json': json.dumps(income_data),
        'expense_json': json.dumps(expense_data),
        'rows': rows,
        'selected_year': year,
        'selected_month': month,
        'years': range(today.year - 3, today.year + 1),
        'months': [
            (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
            (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
            (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
        ],
    }
    return render(request, 'resources/department_comparison.html', context)