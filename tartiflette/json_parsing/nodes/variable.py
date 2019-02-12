from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import NamedNodeMixin


class VariableNode(NamedNodeMixin, Node):
    KIND = "Variable"
