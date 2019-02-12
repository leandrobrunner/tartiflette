from tartiflette.json_parsing.nodes.base import Node
from tartiflette.json_parsing.nodes.mixins import (
    TypeConditionedNodeMixin,
    WithDirectivesNodeMixin,
    WithSelectionSetNodeMixin,
)


class InlineFragmentNode(
    WithDirectivesNodeMixin,
    TypeConditionedNodeMixin,
    WithSelectionSetNodeMixin,
    Node,
):
    KIND = "InlineFragment"
