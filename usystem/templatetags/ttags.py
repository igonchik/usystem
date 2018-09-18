from django import template
from collections import defaultdict
from datetime import datetime

register = template.Library()


class TreeNode(template.Node):
    def __init__(self, tree, node_list):
        self.tree = tree
        self.node_list = node_list

    def render(self, context):
        tree = self.tree.resolve(context)

        # итератор по входному списку, выдающий пары вида
        # (элемент списка, его подсписок), причём одного из элемента пары
        # может не быть
        def pairs(items):

            # внутренний "грязный" генератор, выдающий пары, где могут быть
            # бесполезные: с обоими пустыми head и tail
            def dirty(items):
                items = iter(items)
                head = None
                try:
                    while True:
                        item = items.__next__()
                        if isinstance(item, (list, tuple)):
                            yield head, item
                            head = None
                        else:
                            yield head, None
                            head = item
                except StopIteration:
                    yield head, None

            # фильтр над грязным генератором, удаляющий бесполезные пары
            return ((h, t) for h, t in dirty(items) if h or t)

        # выводит элемент списка с подсписком
        # для подсписка рекурсивно вызывается render_items
        def render_item(item, sub_items, level):
            css = ''
            if sub_items:
                css = 'data-sys="0" data-icon="<span class=\'mif-bookmarks\'></span>"'
            elif item.alias == 'Ожидают авторизации':
                css = 'data-sys="1" data-icon="<span class=\'mif-user-secret\'></span>"'
            return ''.join([
                '<li data-path="{2}" data-caption="{0}" {1}>'.format(item.alias, css, item.id),
                item and self.node_list.render(template.Context({'item': item, 'level': level})) or '',
                sub_items and '<ul>%s</ul>' % ''.join(render_items(sub_items, level + 1)) or '',
                '</li>'
            ])

        # вывод списка элементов
        def render_items(items, level):
            return ''.join(render_item(h, t, level) for h, t in pairs(items))

        return render_items(tree, 0)


@register.tag
def tree(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError('"%s" takes one argument: tree-structured list' % bits[0])
    node_list = parser.parse('end' + bits[0])
    parser.delete_first_token()
    return TreeNode(parser.compile_filter(bits[1]), node_list)


@register.filter
def astree(items, attribute):

    # перевод списка в dict: parent -> список детей
    parent_map = defaultdict(list)
    for item in items:
        parent_map[getattr(item, attribute)].append(item)

    # рекурсивный вывод детей одного parent'а
    def tree_level(parent):
        for item in parent_map[parent]:
            yield item
            sub_items = list(tree_level(item.id))
            if sub_items:
                yield sub_items

    return list(tree_level(None))


@register.filter
def x509Valid(item):
    return False


@register.filter
def kbytes_2_human_readable(number_of_bytes):
    if number_of_bytes < 0:
        raise ValueError("!!! number_of_bytes can't be smaller than 0 !!!")

    step_to_greater_unit = 1024.
    number_of_bytes = float(number_of_bytes)
    unit = 'KB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'MB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'GB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'TB'

    precision = 2
    number_of_bytes = round(number_of_bytes, precision)
    return str(number_of_bytes) + ' ' + unit


@register.filter
def bytes_2_human_readable(number_of_bytes):
    if number_of_bytes < 0:
        raise ValueError("!!! number_of_bytes can't be smaller than 0 !!!")

    step_to_greater_unit = 1024.
    number_of_bytes = float(number_of_bytes)
    unit = 'bytes'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'KB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'MB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'GB'

    if (number_of_bytes / step_to_greater_unit) >= 1:
        number_of_bytes /= step_to_greater_unit
        unit = 'TB'

    precision = 2
    number_of_bytes = round(number_of_bytes, precision)
    return str(number_of_bytes) + ' ' + unit


@register.filter
def x509timestamp(item):
    return datetime(int(item[0:4]), int(item[4:6]), int(item[6:8]), int(item[8:10]), int(item[10:12]), int(item[12:14]))
