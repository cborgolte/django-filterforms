#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A FilterForm is a Django Form that provides a method to filter querysets dependending on
the users input.

Typicall use cases are:
    - Filtering for intervals on numeric data
    - Filtering for (case insensitive) substrings of character data

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
            FilterType(label='Author', field='author', fieldtype='CharField', filtermethod='icontains', args={'required': False}),

            # Number of Pages [______] - [_______]
            FilterType(label='Number of Pages', field='pages', fieldtype='IntegerField', filtermethod='minmax', args={'required': False}),

            # Price Range [______] - [_______]
            FilterType(label='Price Range', field='price', fieldtype='DecimalField', filtermethod='minmax', args={'required': False})
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

# mapping of non django filter types
FILTERMETHODS = dict(minmax=('gte', 'lte'))

# A list of FilterTypes will be used to setup the filter form
FilterType = collections.namedtuple('FilterType', 'label, field, fieldtype, filtermethod, args')

def filterform_factory(filtertypes):
    """
    Returns a FilterForm class with given filter types.

    A FilterForm provides the method `filter(queryset)` to filter a given queryset by
    values entered by the user.
    """

    class _FilterForm(forms.Form):
        """The inner form class is an empty Django Form that gets its fields dynamically."""

        def __init__(self, *args, **kwargs):
            """Dynamically insert fields according to given filtertypes."""
            super(_FilterForm, self).__init__(*args, **kwargs)
            for filtertype in filtertypes:
                filtermethods = FILTERMETHODS.get(filtertype.filtermethod, filtertype.filtermethod)
                if isinstance(filtermethods, str):
                    filtermethods = [filtermethods]
                for filtermthd in filtermethods:
                    args = filtertype.args
                    args['label'] = filtertype.label
                    self.fields['{0}__{1}'.format(filtertype.field, filtermthd).rstrip('_')] =\
                            getattr(forms, filtertype.fieldtype)(**args)

        def filter(self, query):
            """Performs filtering on a queryset.

            Requires the form to be valid."""
            if not self.is_valid():
                raise RuntimeError('You should handle form validation before calling filter()')
            filters = dict((k, v) for (k, v) in self.cleaned_data.items() if v)
            return query.filter(**filters)
    return _FilterForm
