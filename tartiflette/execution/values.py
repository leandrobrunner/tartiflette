from typing import Any, Dict, List, Optional, Union

from tartiflette.error.base import GraphQLError
from tartiflette.json_parsing.nodes import (
    ListTypeNode,
    NamedTypeNode,
    NonNullTypeNode,
)
from tartiflette.types.list import GraphQLList
from tartiflette.types.non_null import GraphQLNonNull
from tartiflette.validations.validators import is_input_type, is_non_null_type


def type_from_ast(
    schema: "GraphQLSchema",
    type_node: Union["ListTypeNode", "NonNullTypeNode", "NamedTypeNode"],
) -> "GraphQLType":
    if isinstance(type_node, ListTypeNode):
        return GraphQLList(type_from_ast(schema, type_node.type_reference))
    if isinstance(type_node, NonNullTypeNode):
        return GraphQLNonNull(type_from_ast(schema, type_node.type_reference))
    if isinstance(type_node, NamedTypeNode):
        return schema.find_type(type_node.name.value)


def coerce_variable_values(
    schema: "GraphQLSchema",
    validation_context: "ValidationContext",
    variable_definitions: List["VariableDefinitionNode"],
    variable_values: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not variable_values:
        return {}

    print(">> coerce_variable_values")

    coerced_values = {}
    for variable_definition in variable_definitions:
        var_name = variable_definition.variable.name.value
        var_type = type_from_ast(schema, variable_definition.type_reference)

        if not is_input_type(var_type):
            validation_context.add_error(
                GraphQLError(
                    "Variable < $%s > expected value of type < %s > which "
                    "cannot be used as an input type."
                    % (var_name, variable_definition.type_reference)
                )
            )
            continue

        has_value = var_name in variable_values
        value = variable_values.get(var_name)

        if not has_value and variable_definition.default_value:
            coerced_values[var_name] = variable_definition.default_value.value
        elif (not has_value or value is None) and is_non_null_type(var_type):
            if has_value:
                validation_context.add_error(
                    GraphQLError(
                        "Variable < $%s > of non-null type < %s > must not be "
                        "null." % (var_name, var_type)
                    )
                )
            else:
                validation_context.add_error(
                    GraphQLError(
                        "Variable < $%s > of required type < %s > was not "
                        "provided." % (var_name, var_type)
                    )
                )
        elif has_value:
            # TODO: maybe we should implement a ù coerce_value` function which
            # coerce the provided value the expected type or returns errors if
            # impossible.
            coerced_values[var_name] = value

    return coerced_values
