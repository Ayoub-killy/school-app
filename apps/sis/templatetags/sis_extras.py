from django import template

register = template.Library()


@register.filter
def semester_label(semester, level):
    return semester.label_for_level(level)