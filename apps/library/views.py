from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from apps.core.decorators import role_required
from .forms import BookCategoryForm, BookForm, BookCopyForm, LibraryMemberForm, LoanIssueForm
from .models import BookCategory, Book, BookCopy, LibraryMember, Loan
from .forms import BulkCopyForm

LIB_ROLES = ('LIBRARIAN', 'HEAD_OF_SCHOOL', 'ADMIN')


@role_required(*LIB_ROLES)
def bookcategory_list(request):
    categories = BookCategory.objects.all()
    return render(request, 'library/bookcategory_list.html', {'categories': categories})


@role_required(*LIB_ROLES)
def bookcategory_create(request):
    if request.method == 'POST':
        form = BookCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book category created successfully.')
            return redirect('library:bookcategory_list')
    else:
        form = BookCategoryForm()
    return render(request, 'library/bookcategory_form.html', {'form': form})


@role_required(*LIB_ROLES)
def bookcategory_update(request, pk):
    category = get_object_or_404(BookCategory, pk=pk)
    if request.method == 'POST':
        form = BookCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book category updated successfully.')
            return redirect('library:bookcategory_list')
    else:
        form = BookCategoryForm(instance=category)
    return render(request, 'library/bookcategory_form.html', {'form': form, 'category': category})


@role_required(*LIB_ROLES)
def bookcategory_delete(request, pk):
    category = get_object_or_404(BookCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Book category deleted successfully.')
        return redirect('library:bookcategory_list')
    return render(request, 'library/bookcategory_confirm_delete.html', {'category': category})


@role_required(*LIB_ROLES)
def book_list(request):
    books = Book.objects.select_related('category').all()
    return render(request, 'library/book_list.html', {'books': books})


@role_required(*LIB_ROLES)
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book created successfully.')
            return redirect('library:book_list')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form})


@role_required(*LIB_ROLES)
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Book updated successfully.')
            return redirect('library:book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'library/book_form.html', {'form': form, 'book': book})


@role_required(*LIB_ROLES)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Book deleted successfully.')
        return redirect('library:book_list')
    return render(request, 'library/book_confirm_delete.html', {'book': book})


@role_required(*LIB_ROLES)
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    copies = book.copies.all()

    if request.method == 'POST':
        form = BulkCopyForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']

            existing_numbers = []
            for c in copies:
                digits = ''.join(ch for ch in c.copy_number if ch.isdigit())
                if digits:
                    existing_numbers.append(int(digits))
            next_number = (max(existing_numbers) + 1) if existing_numbers else 1

            new_copies = [
                BookCopy(book=book, copy_number=f"{next_number + i}", status='AVAILABLE')
                for i in range(quantity)
            ]
            BookCopy.objects.bulk_create(new_copies)

            messages.success(request, f'{quantity} copies added successfully (Copy {next_number} - Copy {next_number + quantity - 1}).')
            return redirect('library:book_detail', pk=book.pk)
    else:
        form = BulkCopyForm()

    return render(request, 'library/book_detail.html', {'book': book, 'copies': copies, 'form': form})


@role_required(*LIB_ROLES)
def copy_delete(request, pk):
    copy = get_object_or_404(BookCopy, pk=pk)
    book_pk = copy.book.pk
    if request.method == 'POST':
        copy.delete()
        messages.success(request, 'Copy deleted successfully.')
    return redirect('library:book_detail', pk=book_pk)


@role_required(*LIB_ROLES)
def member_list(request):
    members = LibraryMember.objects.select_related('student', 'staff').all()
    return render(request, 'library/member_list.html', {'members': members})


@role_required(*LIB_ROLES)
def member_create(request):
    if request.method == 'POST':
        form = LibraryMemberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Library member registered successfully.')
            return redirect('library:member_list')
    else:
        form = LibraryMemberForm()
    return render(request, 'library/member_form.html', {'form': form})


@role_required(*LIB_ROLES)
def member_update(request, pk):
    member = get_object_or_404(LibraryMember, pk=pk)
    if request.method == 'POST':
        form = LibraryMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, 'Library member updated successfully.')
            return redirect('library:member_list')
    else:
        form = LibraryMemberForm(instance=member)
    return render(request, 'library/member_form.html', {'form': form, 'member': member})


@role_required(*LIB_ROLES)
def member_delete(request, pk):
    member = get_object_or_404(LibraryMember, pk=pk)
    if request.method == 'POST':
        member.delete()
        messages.success(request, 'Library member deleted successfully.')
        return redirect('library:member_list')
    return render(request, 'library/member_confirm_delete.html', {'member': member})


@role_required(*LIB_ROLES)
def loan_list(request):
    active_loans = Loan.objects.select_related('book_copy__book', 'member').filter(returned_date__isnull=True)
    return render(request, 'library/loan_list.html', {'loans': active_loans})


@role_required(*LIB_ROLES)
def loan_issue(request):
    if request.method == 'POST':
        form = LoanIssueForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.issued_by = request.user
            loan.save()
            loan.book_copy.status = 'BORROWED'
            loan.book_copy.save()
            messages.success(request, 'Book issued successfully.')
            return redirect('library:loan_list')
    else:
        form = LoanIssueForm()
    return render(request, 'library/loan_issue_form.html', {'form': form})


@role_required(*LIB_ROLES)
def loan_return(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    if request.method == 'POST':
        loan.returned_date = timezone.now().date()
        loan.save()
        loan.book_copy.status = 'AVAILABLE'
        loan.book_copy.save()
        messages.success(request, 'Book returned successfully.')
        return redirect('library:loan_list')
    return render(request, 'library/loan_return_confirm.html', {'loan': loan})
