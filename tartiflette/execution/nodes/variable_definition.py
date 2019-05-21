from functools import partial
from typing import Any, Callable

from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.execution.values import variable_definition_coercer
from tartiflette.utils.coerce_value import get_variable_definition_coercer
from tartiflette.utils.type_from_ast import schema_type_from_ast
from tartiflette.utils.value_from_ast import value_from_ast


class ExecutableVariableDefinition:
    """
    TODO:
    """

    __slots__ = (
        "name",
        "graphql_type",
        "default_value",
        "coercer",
        "definition",
    )

    def __init__(
        self,
        name: str,
        graphql_type: "GraphQLType",
        default_value: Any,
        coercer: Callable,
        definition: "VariableDefinitionNode",
    ) -> None:
        """
        :param name: TODO:
        :param graphql_type: TODO:
        :param default_value: TODO:
        :param coercer: TODO:
        :param definition_node: TODO:
        :type name: TODO:
        :type graphql_type: TODO:
        :type default_value: TODO:
        :type coercer: TODO:
        :type definition_node: TODO:
        """
        self.name = name
        self.graphql_type = graphql_type
        self.default_value = default_value
        self.coercer = partial(coercer, self)
        self.definition = definition


def variable_definition_node_to_executable(
    schema: "GraphQLSchema", variable_definition_node: "VariableDefinitionNode"
) -> "ExecutableVariableDefinition":
    """
    TODO:
    :param schema: TODO:
    :param variable_definition_node: TODO:
    :type schema: TODO:
    :type variable_definition_node: TODO:
    :return: TODO:
    :rtype: TODO:
    """
    graphql_type = schema_type_from_ast(schema, variable_definition_node.type)
    return ExecutableVariableDefinition(
        name=variable_definition_node.variable.name.value,
        graphql_type=graphql_type,
        default_value=(
            value_from_ast(
                variable_definition_node.default_value, graphql_type
            )
            if variable_definition_node.default_value
            else UNDEFINED_VALUE
        ),
        coercer=partial(
            variable_definition_coercer,
            input_coercer=partial(
                get_variable_definition_coercer(graphql_type),
                variable_definition_node,
            ),
        ),
        definition=variable_definition_node,
    )
