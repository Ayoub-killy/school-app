from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse

from apps.core.decorators import role_required
from apps.accounts.models import User
from apps.sis.models import Stream

from .models import SubjectTeacherAssignment, Timetable, TimetableEntry, Period
from .forms import SubjectTeacherAssignmentForm
from . import services

TIMETABLE_MANAGERS = (User.Role.ACADEMIC_MASTER, User.Role.HEAD_OF_SCHOOL)


@role_required(*TIMETABLE_MANAGERS)
def assignment_list(request):
    assignments = SubjectTeacherAssignment.objects.select_related(
        'stream__school_class', 'subject', 'teacher'
    ).all()
    return render(request, 'timetable/assignment_list.html', {'assignments': assignments})


@role_required(*TIMETABLE_MANAGERS)
def assignment_create(request):
    if request.method == 'POST':
        form = SubjectTeacherAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.save()
            messages.success(request, "Assignment saved.")
            return redirect('timetable:assignment_list')
    else:
        form = SubjectTeacherAssignmentForm()
    return render(request, 'timetable/assignment_form.html', {'form': form})


@role_required(*TIMETABLE_MANAGERS)
def assignment_update(request, pk):
    assignment = get_object_or_404(SubjectTeacherAssignment, pk=pk)
    if request.method == 'POST':
        form = SubjectTeacherAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            form.save()
            messages.success(request, "Assignment updated.")
            return redirect('timetable:assignment_list')
    else:
        form = SubjectTeacherAssignmentForm(instance=assignment)
    return render(request, 'timetable/assignment_form.html', {'form': form, 'assignment': assignment})


@role_required(*TIMETABLE_MANAGERS)
def assignment_delete(request, pk):
    assignment = get_object_or_404(SubjectTeacherAssignment, pk=pk)
    if request.method == 'POST':
        assignment.delete()
        messages.success(request, "Assignment removed.")
        return redirect('timetable:assignment_list')
    return render(request, 'timetable/assignment_confirm_delete.html', {'assignment': assignment})


@role_required(*TIMETABLE_MANAGERS)
def generate_timetable_view(request):
    active = Timetable.objects.filter(is_active=True).first()

    if request.method == 'POST':
        try:
            timetable = services.generate_timetable(request.user)
        except services.TimetableGenerationError as exc:
            messages.error(request, str(exc))
            return redirect('timetable:generate')

        sent, skipped = services.notify_teachers(timetable)
        messages.success(request, f"New timetable generated and emailed to {sent} teacher(s).")
        if skipped:
            names = ", ".join(t.get_full_name() or t.username for t in skipped)
            messages.warning(request, f"No email on file for: {names}. They were not notified.")
        return redirect('timetable:view')

    return render(request, 'timetable/generate_confirm.html', {'active': active})


@role_required(*TIMETABLE_MANAGERS)
def timetable_view(request):
    streams = Stream.objects.select_related('school_class').all()
    stream_id = request.GET.get('stream')
    selected_stream = None

    if stream_id:
        selected_stream = get_object_or_404(Stream, pk=stream_id)
    elif streams:
        selected_stream = streams[0]

    periods = Period.objects.filter(period_type=Period.PeriodType.TEACHING).order_by('order')
    days = TimetableEntry.Day.choices

    grid = {day: {} for day, _ in days}
    if selected_stream:
        entries = TimetableEntry.objects.filter(
            timetable__is_active=True, stream=selected_stream
        ).select_related('subject', 'teacher', 'period')
        for entry in entries:
            grid[entry.day][entry.period_id] = entry

    return render(request, 'timetable/timetable_view.html', {
        'streams': streams,
        'selected_stream': selected_stream,
        'periods': periods,
        'days': days,
        'grid': grid,
    })


@role_required(*TIMETABLE_MANAGERS)
def timetable_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm

    active = Timetable.objects.filter(is_active=True).first()
    if not active:
        messages.error(request, "No active timetable to export. Generate one first.")
        return redirect('timetable:generate')

    periods = list(Period.objects.filter(period_type=Period.PeriodType.TEACHING).order_by('order'))
    days = TimetableEntry.Day.choices
    streams = Stream.objects.select_related('school_class').all()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="school_timetable.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(A4), topMargin=1 * cm, bottomMargin=1 * cm)
    styles = getSampleStyleSheet()
    elements = []

    for i, stream in enumerate(streams):
        entries = TimetableEntry.objects.filter(timetable=active, stream=stream).select_related('subject', 'teacher', 'period')
        lookup = {(e.day, e.period_id): e for e in entries}

        elements.append(Paragraph(f"{stream} — Weekly Teaching Timetable", styles['Heading2']))
        elements.append(Spacer(1, 0.3 * cm))

        header = ['Period'] + [label for _, label in days]
        table_data = [header]
        for period in periods:
            row = [f"{period.label}\n{period.start_time.strftime('%H:%M')}-{period.end_time.strftime('%H:%M')}"]
            for day_code, _ in days:
                entry = lookup.get((day_code, period.id))
                row.append(f"{entry.subject.name}\n{entry.teacher.get_full_name() or entry.teacher.username}" if entry else "—")
            table_data.append(row)

        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(table)

        if i < len(streams) - 1:
            elements.append(PageBreak())

    doc.build(elements)
    return response
