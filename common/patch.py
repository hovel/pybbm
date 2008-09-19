import django.newforms

def as_p(self):
    """
    Returns this form rendered as HTML <p>s.
    
    This is modified version of original as_p. 
    Actually it wraps content into fieldset tag.
    """

    return self._html_output(u'<fieldset><div class="label">%(label)s</div><div class="form"> %(errors)s %(field)s%(help_text)s</div></fieldset>', u'%s', '</fieldset>',
                             u' <span class="note">%s</span>', False)

# OMG
django.newforms.BaseForm.as_p = as_p

def text_input_init(self, *args, **kwargs):
    kwargs.setdefault('attrs', {}).setdefault('class', '')
    kwargs['attrs']['class'] += ' text'
    super(self.__class__, self).__init__(*args, **kwargs)

django.newforms.widgets.TextInput.__init__ = text_input_init

# TODO: it does not work
#django.newforms.widgets.TextInput.__init__ = text_input_init
