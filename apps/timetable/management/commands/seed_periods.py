from datetime import time
from django.core.management.base import BaseCommand
from apps.timetable.models import Period


SCHEDULE = [
    (1, 'First Period', time(7, 30), time(8, 50), Period.PeriodType.TEACHING),
    (2, 'Second Period', time(8, 50), time(10, 10), Period.PeriodType.TEACHING),
    (3, 'Tea Break', time(10, 10), time(10, 40), Period.PeriodType.BREAK),
    (4, 'Third Period', time(10, 40), time(11, 40), Period.PeriodType.TEACHING),
    (5, 'Fourth Period', time(11, 40), time(12, 40), Period.PeriodType.TEACHING),
    (6, 'Short Break', time(12, 40), time(12, 45), Period.PeriodType.BREAK),
    (7, 'Fifth Period', time(12, 45), time(14, 5), Period.PeriodType.TEACHING),
]


class Command(BaseCommand):
    help = "Seeds (or updates) the fixed daily Period lookup table used by the timetable generator."

    def handle(self, *args, **options):
        for order, label, start, end, period_type in SCHEDULE:
            period, created = Period.objects.update_or_create(
                order=order,
                defaults={'label': label, 'start_time': start, 'end_time': end, 'period_type': period_type},
            )
            verb = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{verb}: {period}"))

        self.stdout.write(self.style.SUCCESS("Period schedule seeded successfully."))
