from .models import SchoolClass
from django import forms
from django.contrib.auth.forms import UserCreationForm
from apps.accounts.models import User
from .models import Student, Stream, Combination, Staff


class StreamSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            try:
                stream = Stream.objects.get(pk=value.value)
                option['attrs']['data-class-id'] = str(stream.school_class_id)
                option['attrs']['data-category'] = stream.category or ''
            except Stream.DoesNotExist:
                pass
        return option


class CombinationSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            try:
                combo = Combination.objects.get(pk=value.value)
                option['attrs']['data-category'] = combo.category
            except Combination.DoesNotExist:
                pass
        return option


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name', 'middle_name', 'last_name',
            'date_of_birth', 'gender', 'stream', 'combination', 'status', 'leaving_year',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'stream': StreamSelect(attrs={'class': 'form-select'}),
            'combination': CombinationSelect(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'leaving_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2026'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['stream'].required = True
        self.fields['stream'].empty_label = "-- Select Stream --"
        self.fields['combination'].required = False
        self.fields['combination'].empty_label = "-- Select Combination --"

    def clean(self):
        cleaned_data = super().clean()
        stream = cleaned_data.get('stream')
        combination = cleaned_data.get('combination')
        status = cleaned_data.get('status')
        leaving_year = cleaned_data.get('leaving_year')

        if stream and stream.category:
            if not combination:
                raise forms.ValidationError(
                    f"This stream requires a Combination ({stream.get_category_display()})."
                )
            if combination.category != stream.category:
                raise forms.ValidationError(
                    "The selected Combination doesn't match this Stream's category."
                )
        elif stream and not stream.category:
            cleaned_data['combination'] = None

        if status == 'GRADUATED' and not leaving_year:
            raise forms.ValidationError("Please enter the Year of Graduation.")

        return cleaned_data

    def save(self, commit=True):
        student = super().save(commit=False)
        if student.status == 'GRADUATED' and student.stream:
            student.leaving_class = student.stream.school_class.name
        if commit:
            student.save()
        return student


class StaffUserForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=[
            (User.Role.TEACHER, 'Teacher'),
            (User.Role.LIBRARIAN, 'Librarian'),
            (User.Role.ACCOUNTANT, 'Accountant'),
            (User.Role.ADMIN, 'Administrator'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['department', 'date_of_birth', 'gender', 'phone_number', 'address', 'photo']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
from .models import Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description', 'head']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'head': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head'].required = False
        self.fields['head'].empty_label = "-- No Head Assigned --"
from .models import Combination as CombinationModel


class CombinationForm(forms.ModelForm):
    class Meta:
        model = CombinationModel
        fields = ['code', 'full_name', 'category']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }
from .models import Subject


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'department', 'levels', 'teachers']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'levels': forms.Select(attrs={'class': 'form-select'}),
            'teachers': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
from .models import SchoolClass


class SchoolClassForm(forms.ModelForm):
    class Meta:
        model = SchoolClass
        fields = ['name', 'level', 'order', 'class_teacher']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'class_teacher': forms.Select(attrs={'class': 'form-select'}),
        }
from .models import Stream as StreamModel


class SchoolClassSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            try:
                sc = SchoolClass.objects.get(pk=value.value)
                option['attrs']['data-level'] = sc.level
            except SchoolClass.DoesNotExist:
                pass
        return option


class StreamForm(forms.ModelForm):
    class Meta:
        model = StreamModel
        fields = ['school_class', 'name', 'category', 'combination', 'olevel_categories']
        widgets = {
            'school_class': SchoolClassSelect(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'combination': forms.Select(attrs={'class': 'form-select'}),
            'olevel_categories': forms.CheckboxSelectMultiple(),
        }


from .models import Guardian


class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ['first_name', 'middle_name', 'last_name', 'phone_number', 'email', 'address', 'occupation']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
        }
from .models import OLevelCategory


class OLevelCategoryForm(forms.ModelForm):
    class Meta:
        model = OLevelCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

from .models import AcademicYear, Semester


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['year', 'is_active']
        widgets = {
            'year': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ['academic_year', 'name', 'start_date', 'end_date', 'is_active']
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        
class StudentImportForm(forms.Form):
    excel_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.xlsx'})
        )
    
from .models import Term


class TermForm(forms.ModelForm):
    class Meta:
        model = Term
        fields = ['semester', 'name', 'start_date', 'end_date', 'is_active']
        widgets = {
            'semester': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

from .models import TeachingScheduleEntry, LessonPlan, Topic, SubTopic


class TeachingScheduleEntryForm(forms.ModelForm):
    class Meta:
        model = TeachingScheduleEntry
        fields = ['stream', 'subject', 'day', 'start_time', 'end_time']
        widgets = {
            'stream': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'day': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['subject'].queryset = Subject.objects.filter(teachers=teacher)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise forms.ValidationError("End time must be after start time.")
        return cleaned_data


class LessonPlanForm(forms.ModelForm):
    class Meta:
        model = LessonPlan
        fields = ['stream', 'subject', 'start_date', 'end_date']
        widgets = {
            'stream': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['subject'].queryset = Subject.objects.filter(teachers=teacher)

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start >= end:
            raise forms.ValidationError("End date must be after start date.")
        return cleaned_data


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Topic title'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px;'}),
        }


class SubTopicForm(forms.ModelForm):
    class Meta:
        model = SubTopic
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subtopic title'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px;'}),
        }

