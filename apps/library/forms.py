from django import forms
from .models import BookCategory, Book, BookCopy, LibraryMember, Loan

class BookCategoryForm(forms.ModelForm):
    class Meta:
        model = BookCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publisher', 'year_published', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'year_published': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class BookCopyForm(forms.ModelForm):
    class Meta:
        model = BookCopy
        fields = ['book', 'copy_number', 'status']
        widgets = {
            'book': forms.HiddenInput(),
            'copy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

class LibraryMemberForm(forms.ModelForm):
    class Meta:
        model = LibraryMember
        fields = [
            'member_type', 'student', 'staff',
            'external_full_name', 'external_phone', 'external_relationship',
            'is_active'
        ]
        widgets = {
            'member_type': forms.Select(attrs={'class': 'form-select', 'id': 'id_member_type'}),
            'student': forms.Select(attrs={'class': 'form-select'}),
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'external_full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'external_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'external_relationship': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these optional at the form level, custom validation handles the rest
        self.fields['student'].required = False
        self.fields['staff'].required = False
        self.fields['external_full_name'].required = False

    def clean(self):
        # Custom validation to ensure the correct identity is provided based on member_type
        cleaned_data = super().clean()
        member_type = cleaned_data.get('member_type')
        student = cleaned_data.get('student')
        staff = cleaned_data.get('staff')
        external_full_name = cleaned_data.get('external_full_name')

        if member_type == 'STUDENT' and not student:
            raise forms.ValidationError("Select a Student when member type is Student.")
        if member_type == 'STAFF' and not staff:
            raise forms.ValidationError("Select a Staff member when member type is Staff.")
        if member_type == 'EXTERNAL' and not external_full_name:
            raise forms.ValidationError("Full name is required for external members.")

        return cleaned_data

class LoanIssueForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['book_copy', 'member', 'borrowed_date', 'due_date']
        widgets = {
            'book_copy': forms.Select(attrs={'class': 'form-select'}),
            'member': forms.Select(attrs={'class': 'form-select'}),
            'borrowed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show copies that are actually available to lend
        self.fields['book_copy'].queryset = BookCopy.objects.filter(status='AVAILABLE')
    
class BulkCopyForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1, max_value=500,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="How many new copies to add"
    )
