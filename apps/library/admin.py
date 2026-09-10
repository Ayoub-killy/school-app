from django.contrib import admin
from .models import BookCategory, Book, BookCopy, LibraryMember, Loan


@admin.register(BookCategory)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'isbn']
    list_filter = ['category']
    search_fields = ['title', 'author', 'isbn']


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    list_display = ['book', 'copy_number', 'status']
    list_filter = ['status']


@admin.register(LibraryMember)
class LibraryMemberAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'date_joined', 'is_active']
    list_filter = ['is_active']


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['book_copy', 'member', 'borrowed_date', 'due_date', 'returned_date']
    list_filter = ['borrowed_date']
    