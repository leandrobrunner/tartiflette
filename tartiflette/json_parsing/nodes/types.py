from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import TypeReferencedNodeMixin


class ListTypeNode(TypeReferencedNodeMixin, Node):
    KIND = "ListType"


class NonNullTypeNode(TypeReferencedNodeMixin, Node):
    KIND = "NonNullType"
