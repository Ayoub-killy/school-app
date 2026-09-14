from django import forms
from django.core.exceptions import ValidationError
from .models import SubjectTeacherAssignment


class SubjectTeacherAssignmentForm(forms.ModelForm):
    class Meta:
        model = SubjectTeacherAssignment
        fields = ['stream', 'subject', 'teacher']
        widgets = {
            'stream': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        stream = cleaned_data.get('stream')
        subject = cleaned_data.get('subject')

        if stream and subject:
            qs = SubjectTeacherAssignment.objects.filter(stream=stream, subject=subject)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"{subject} is already assigned to a teacher for {stream}.")

            level = stream.school_class.level
            if subject.levels != 'BOTH' and subject.levels != level:
                raise ValidationError(
                    f"{subject} is not offered at {stream.school_class.get_level_display()}."
                )
        return cleaned_data
