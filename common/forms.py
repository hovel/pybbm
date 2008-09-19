from django import forms

def build_form(Form, _request, GET=False, *args, **kwargs):
    """
    Shorcut for building the form instance of given class.
    """

    if not GET and 'POST' == _request.method:
        form = Form(_request.POST, _request.FILES, *args, **kwargs)
    elif GET and 'GET' == _request.method:
        form = Form(_request.GET, _request.FILES, *args, **kwargs)
    else:
        form = Form(*args, **kwargs)
    return form
