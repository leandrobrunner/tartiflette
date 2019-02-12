from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import (
    NamedNodeMixin,
    WithDirectivesNodeMixin,
)


class FragmentSpreadNode(NamedNodeMixin, WithDirectivesNodeMixin, Node):
    KIND = "FragmentSpread"
