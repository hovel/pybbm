from django import template

register = template.Library()

@register.tag(name='set')
def do_set(parser, token):
    try:
        tag_name, name, value = token.contents.split(None, 2)
    except ValueError:
        raise template.TemplateSyntaxError("'captureas' node requires a variable name and value.")
    #parser.delete_first_token()
    return SetNode(name, value)

class SetNode(template.Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def render(self, context):
        context[self.name] = self.value
        return ''
