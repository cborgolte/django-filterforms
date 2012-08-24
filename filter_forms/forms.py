#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A FilterForm is a Django Form that provides a method to filter querysets dependending on
the users input.

Example:

    models.py:

        class Book(Model):
            author = CharField(...)
            title = CharField(...)
            pages = IntegerField(...)
            price = DecimalField(...)


    forms.py:

        BookFilterForm = filterform_factory(
            # Author [____________]
            create_field(label='Author', field='author', fieldtype='CharField', filtermethod='icontains', args={'required': False}),

            # Number of Pages [______] - [_______]
            create_field(label='Number of Pages', field='pages', fieldtype='IntegerField', filtermethod='minmax', args={'required': False}),

            # Price Range [______] - [_______]
            create_field(label='Price Range', field='price', fieldtype='DecimalField', filtermethod='range', args={'required': False})
        )


    views.py:

        def book_search(request):
            results = []
            bookfilterform = BookFilterForm(request.REQUEST)
            if bookfilterform.is_valid():
                results = bookfilterform.filter(Book.objects.all())
            return render('templates/booksearch.html', {'results': results})

"""

import collections
from django import forms
from django.template.loader import render_to_string
from django.forms.fields import EMPTY_VALUES
from django.utils.translation import ugettext as _


# see: http://djangosnippets.org/snippets/1104/
class RangeWidget(forms.MultiWidget):
    def __init__(self, widget, *args, **kwargs):
        widgets = (widget, widget)
        super(RangeWidget, self).__init__(widgets=widgets, *args, **kwargs)

    def decompress(self, value):
        return value

    def format_output(self, rendered_widgets):
        out = u' - '.join(rendered_widgets)
        out = u'<div class="range-input">{0}</div>'.format(out)
        return out


def rangefield_factory(field_class):
    class _RangeField(forms.MultiValueField):
        default_error_messages = {
            'invalid_start': _(u'Enter a valid start value.'),
            'invalid_end': _(u'Enter a valid end value.'),
        }

        def __init__(self, widget=field_class.widget, *args, **kwargs):
            if not 'initial' in kwargs:
                kwargs['initial'] = ['','']
            super(_RangeField, self).__init__(fields=(field_class(), field_class()),
                                              widget=RangeWidget(widget), *args, **kwargs)

        def compress(self, data_list):
            if data_list:
                return [self.fields[0].clean(data_list[0]), self.fields[1].clean(data_list[1])]
            return None
    return _RangeField


# Define some typical RangeField Classes
IntegerRangeField = rangefield_factory(forms.IntegerField)
FloatRangeField = rangefield_factory(forms.FloatField)
DecimalRangeField = rangefield_factory(forms.DecimalField)
CharRangeField = rangefield_factory(forms.CharField)


# mapping of non django filter types
FILTERMETHODS = dict(inner_range=('gte', 'lte'))


# A list of FieldDescription will be used to setup the filter form
FieldDescription = collections.namedtuple('FieldDescription', 'label, field, fieldtype, filtermethod, args, widget, widget_attrs')


def create_field(label, field, fieldtype, filtermethod='', args=None, widget=None, widget_attrs=None):
    """Helper: Create a FieldDescription. Provides some default values."""
    if args == None:
        args = {}
    if widget_attrs == None:
        widget_attrs = {}
    return FieldDescription(label, field, fieldtype, filtermethod, args, widget, widget_attrs)


def filterform_factory(field_descriptions):
    """
    Returns a FilterForm class with given filter types.

    A FilterForm provides the method `filter(queryset)` to filter a given queryset by
    values entered by the user.
    """

    class _FilterForm(forms.Form):
        """This inner form class is an empty Django Form that gets its fields dynamically."""

        def __init__(self, *args, **kwargs):
            """Dynamically insert fields according to given field_descriptions."""
            super(_FilterForm, self).__init__(*args, **kwargs)
            for field_desc in field_descriptions:
                args = field_desc.args
                if field_desc.label:
                    args['label'] = field_desc.label
                FieldClass = globals().get(field_desc.fieldtype, None)
                if not FieldClass:
                    FieldClass = getattr(forms, field_desc.fieldtype)
                widget = None
                if field_desc.widget:
                    widget = globals().get(field_desc.widget, None)
                    if not widget:
                        widget = getattr(forms, field_desc.widget)
                if widget:
                    args['widget'] = widget
                field = FieldClass(**args)
                if field_desc.widget_attrs:
                    field.widget.attrs = field_desc.widget_attrs
                field.filtermethod = field_desc.filtermethod
                self.fields[field_desc.field] = field

        def _field_as_filter(self, fieldname, values):
            """Combine the fieldname with its filtermethod and map it to the entered values.

            Returns a dict with key = fieldname__filtermethod and value = entered form value.

            Examples:
                For a inner_range FieldDescription
                {'size__gt': 10, 'size__lt': 20}

                For an icontains FieldDescription
                {'author__icontains': 'joe abercrombie'}

            """
            field = self.fields[fieldname]
            values = self.cleaned_data[fieldname]
            filtermethods = FILTERMETHODS.get(field.filtermethod, field.filtermethod)
            if isinstance(filtermethods, (tuple, list)):
                assert(isinstance(values, (tuple, list)))
                assert(len(values) == len(filtermethods))
                return dict(('{0}__{1}'.format(fieldname, filtermethod).rstrip('_'), value)
                            for (filtermethod, value) in zip(filtermethods, values))
            return {'{0}__{1}'.format(fieldname, filtermethods).rstrip('_'): values}

        def filter(self, query):
            """Performs filtering on a queryset.

            Requires the form to be valid."""
            if not self.is_valid():
                raise RuntimeError('You should handle form validation before calling filter()')
            filters = dict()
            for (fieldname, values) in self.cleaned_data.items():
                if values:
                    filters.update(self._field_as_filter(fieldname, values))
            retval = query.filter(**filters)
            return retval
    return _FilterForm
