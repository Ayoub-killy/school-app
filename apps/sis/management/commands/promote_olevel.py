from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.sis.models import Student, Stream, SchoolClass


class Command(BaseCommand):
    help = "Promotes O-Level students (Form 1-3) to the next class, and archives Form 4 students as Leavers."

    def handle(self, *args, **options):
        today = timezone.now().date()
        leaving_year = today.year - 1  # e.g. Jan 2027 run archives the 2026 Form 4 batch

        o_level_classes = SchoolClass.objects.filter(level='O_LEVEL').order_by('order')
        class_by_order = {c.order: c for c in o_level_classes}

        promoted_count = 0
        archived_count = 0

        active_students = Student.objects.filter(
            status='ACTIVE',
            stream__school_class__level='O_LEVEL'
        ).select_related('stream__school_class')

        for student in active_students:
            current_class = student.stream.school_class
            next_order = current_class.order + 1

            if next_order in class_by_order:
                next_class = class_by_order[next_order]
                next_stream = Stream.objects.filter(
                    school_class=next_class, name=student.stream.name
                ).first()
                if next_stream:
                    student.stream = next_stream
                    student.save()
                    promoted_count += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f"No matching stream '{student.stream.name}' found in {next_class.name} for {student}"
                    ))
            else:
                # This was the highest O-Level class (Form 4) - archive as Leaver
                student.leaving_year = leaving_year
                student.leaving_class = current_class.name
                student.status = 'GRADUATED'
                student.save()
                archived_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"O-Level promotion complete: {promoted_count} promoted, {archived_count} archived as Leavers."
        ))
