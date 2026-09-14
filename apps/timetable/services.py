import random
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from apps.sis.models import Stream, TeachingScheduleEntry
from .models import Period, SubjectTeacherAssignment, Timetable, TimetableEntry


class TimetableGenerationError(Exception):
    """Raised when no conflict-free timetable could be produced."""
    pass


MAX_ATTEMPTS = 40


def _attempt_fill(streams, periods, days):
    """One randomized attempt at filling every slot for every stream.
    Returns a list of placement dicts, or None if this attempt got stuck.
    """
    stream_quota = {}
    for stream in streams:
        assignments = list(
            SubjectTeacherAssignment.objects.filter(stream=stream).select_related('subject', 'teacher')
        )
        if not assignments:
            continue

        total_slots = len(days) * len(periods)
        base, remainder = divmod(total_slots, len(assignments))
        random.shuffle(assignments)  # who gets the "extra" period each run is randomized

        quota = {}
        for i, assignment in enumerate(assignments):
            quota[assignment.subject_id] = {
                'count': base + (1 if i < remainder else 0),
                'teacher_id': assignment.teacher_id,
            }
        stream_quota[stream.id] = quota

    teacher_busy = {}   # (day, period_id) -> set of teacher_id
    used_today = {}      # (stream_id, day) -> set of subject_id already placed that day
    placements = []

    for day in days:
        for period in periods:
            slot_key = (day, period.id)
            busy = teacher_busy.setdefault(slot_key, set())

            stream_order = list(stream_quota.keys())
            random.shuffle(stream_order)  # randomizes which stream gets first pick each slot

            for stream_id in stream_order:
                quota = stream_quota[stream_id]
                used = used_today.setdefault((stream_id, day), set())

                candidates = [
                    subject_id for subject_id, info in quota.items()
                    if info['count'] > 0
                    and subject_id not in used
                    and info['teacher_id'] not in busy
                ]
                if not candidates:
                    return None  # stuck - caller will retry with a fresh shuffle

                chosen = random.choice(candidates)
                info = quota[chosen]
                info['count'] -= 1
                used.add(chosen)
                busy.add(info['teacher_id'])

                placements.append({
                    'stream_id': stream_id,
                    'day': day,
                    'period_id': period.id,
                    'subject_id': chosen,
                    'teacher_id': info['teacher_id'],
                })

    return placements


def _sync_teaching_schedule(timetable):
    """Fully regenerates every teacher's personal schedule from the active timetable."""
    TeachingScheduleEntry.objects.all().delete()
    entries = TimetableEntry.objects.filter(timetable=timetable).select_related('period')
    TeachingScheduleEntry.objects.bulk_create([
        TeachingScheduleEntry(
            teacher_id=entry.teacher_id,
            stream_id=entry.stream_id,
            subject_id=entry.subject_id,
            day=entry.day,
            start_time=entry.period.start_time,
            end_time=entry.period.end_time,
        )
        for entry in entries
    ])


@transaction.atomic
def generate_timetable(user):
    """Deletes the previous timetable and generates a brand new randomized one.
    Raises TimetableGenerationError if no valid arrangement can be found -
    usually means a teacher is over-assigned across too many overlapping streams.
    """
    streams = list(Stream.objects.all())
    periods = list(Period.objects.filter(period_type=Period.PeriodType.TEACHING).order_by('order'))
    days = [choice[0] for choice in TimetableEntry.Day.choices]

    if not periods:
        raise TimetableGenerationError("No teaching periods configured. Run 'seed_periods' first.")

    for _ in range(MAX_ATTEMPTS):
        placements = _attempt_fill(streams, periods, days)
        if placements is not None:
            break
    else:
        raise TimetableGenerationError(
            "Could not build a conflict-free timetable after several attempts. "
            "Check whether any teacher is assigned to too many overlapping streams/subjects."
        )

    # Previous timetable is fully removed, as required - not archived.
    Timetable.objects.all().delete()
    timetable = Timetable.objects.create(generated_by=user, is_active=True)

    TimetableEntry.objects.bulk_create([
        TimetableEntry(timetable=timetable, **placement) for placement in placements
    ])

    _sync_teaching_schedule(timetable)
    return timetable


def notify_teachers(timetable):
    """Emails every teacher their personal slice of the new timetable."""
    entries = (
        TimetableEntry.objects
        .filter(timetable=timetable)
        .select_related('subject', 'stream', 'period', 'teacher')
        .order_by('teacher_id', 'day', 'period__order')
    )

    by_teacher = {}
    for entry in entries:
        by_teacher.setdefault(entry.teacher, []).append(entry)

    sent, skipped = 0, []
    for teacher, teacher_entries in by_teacher.items():
        if not teacher.email:
            skipped.append(teacher)
            continue

        lines = [f"Hello {teacher.get_full_name() or teacher.username},", "", "Your new teaching schedule:"]
        current_day = None
        for entry in teacher_entries:
            if entry.day != current_day:
                lines.append(f"\n{entry.get_day_display()}:")
                current_day = entry.day
            lines.append(
                f"  {entry.period.label} ({entry.period.start_time.strftime('%H:%M')}"
                f"-{entry.period.end_time.strftime('%H:%M')}): {entry.subject.name} - {entry.stream}"
            )

        send_mail(
            subject="New Teaching Timetable Published",
            message="\n".join(lines),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[teacher.email],
            fail_silently=True,
        )

        sent += 1

    return sent, skipped
