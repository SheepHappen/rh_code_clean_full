import os

from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter
def remove_underscores(value):
    return value.replace('_', ' ')


@register.simple_tag
def svg_icon(filename):
    path = finders.find(os.path.join('svg', '{filename}.svg'.format(filename=filename)), all=True)
    with open(path[0]) as svg_file:
        return mark_safe(svg_file.read())


@register.filter
def svg2data_url(value):
    return "data:image/svg+xml;charset=utf-8;base64, "


@register.filter(needs_autoescape=True)
@stringfilter
def show_more_less(text, show_words=18, autoescape=True):
    print(text)
    show_words = int(show_words)
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    words = esc(text).split()


    if len(words) <= show_words:
        return text

    print(words)
    print('asds')
    insertion = (
        # The see more link...
        '<span class="read-more">'
        'more...'
        '</span>'
    )

    read_less = (
        # The see less link...
        '<span class="read-less">'
        '        less...'
        '</span>'
    )

    words.insert(show_words, '<span class="more d-none">')
    words.append(read_less + '</span>')
    words.append(insertion)

    return mark_safe(' '.join(words))