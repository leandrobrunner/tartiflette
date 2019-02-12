from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import (
    NamedNodeMixin,
    WithArgumentsNodeMixin,
)


class DirectiveNode(NamedNodeMixin, WithArgumentsNodeMixin, Node):
    KIND = "Directive"
