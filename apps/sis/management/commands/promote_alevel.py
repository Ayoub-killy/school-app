from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.sis.models import Student, Stream, SchoolClass


class Command(BaseCommand):
    help = "Promotes A-Level students (Form 5) to Form 6, and archives Form 6 students as Leavers."

    def handle(self, *args, **options):
        today = timezone.now().date()
        leaving_year = today.year  # July 1 archiving uses the current year

        a_level_classes = SchoolClass.objects.filter(level='A_LEVEL').order_by('order')
        class_by_order = {c.order: c for c in a_level_classes}

        promoted_count = 0
        archived_count = 0

        active_students = Student.objects.filter(
            status='ACTIVE',
            stream__school_class__level='A_LEVEL'
        ).select_related('stream__school_class')

        for student in active_students:
            current_class = student.stream.school_class
            next_order = current_class.order + 1

            if next_order in class_by_order:
                next_class = class_by_order[next_order]
                next_stream = Stream.objects.filter(
                    school_class=next_class, category=student.stream.category
                ).first()
                if next_stream:
                    student.stream = next_stream
                    student.combination = student.combination  # combination stays the same
                    student.save()
                    promoted_count += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f"No matching stream for category '{student.stream.category}' found in {next_class.name} for {student}"
                    ))
            else:
                # This was the highest A-Level class (Form 6) - archive as Leaver
                student.leaving_year = leaving_year
                student.leaving_class = current_class.name
                student.status = 'GRADUATED'
                student.save()
                archived_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"A-Level promotion complete: {promoted_count} promoted, {archived_count} archived as Leavers."
        ))
