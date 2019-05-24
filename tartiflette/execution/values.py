import asyncio

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.language.ast import NullValueNode, VariableNode
from tartiflette.types.exceptions import GraphQLError
from tartiflette.types.helpers.definition import (
    is_input_type,
    is_non_null_type,
)
from tartiflette.utils.coerce_value import CoercionResult
from tartiflette.utils.errors import graphql_error_from_nodes
from tartiflette.utils.value_from_ast import value_from_ast
from tartiflette.utils.values import is_invalid_value

__all__ = ["get_argument_values", "coerce_variable_definitions"]


def get_argument_values(
    argument_definitions: Dict[str, "GraphQLArgument"],
    node: Union["FieldNode", "DirectiveNode"],
    variable_values: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    TODO:
    :param argument_definitions: TODO:
    :param node: TODO:
    :param variable_values: TODO:
    :type argument_definitions: TODO:
    :type node: TODO:
    :type variable_values: TODO:
    :return: TODO:
    :rtype: TODO:
    """
    argument_nodes = node.arguments
    if not argument_definitions or argument_nodes is None:
        return {}

    coerced_values = {}
    argument_nodes_map = {
        argument_node.name.value: argument_node
        for argument_node in argument_nodes
    }

    for index, argument_definition in enumerate(
        list(argument_definitions.values())
    ):
        name = argument_definition.name
        arg_type = argument_definition.get_gql_type()
        argument_node = argument_nodes_map.get(name)

        if argument_node and isinstance(argument_node.value, VariableNode):
            variable_name = argument_node.value.name.value
            has_value = variable_values and variable_name in variable_values
            is_null = has_value and variable_values[variable_name] is None
        else:
            has_value = argument_node is not None
            is_null = argument_node and isinstance(
                argument_node.value, NullValueNode
            )

        if not has_value and argument_definition.default_value is not None:
            coerced_values[name] = argument_definition.default_value
        elif (not has_value or is_null) and is_non_null_type(arg_type):
            if is_null:
                raise GraphQLError(
                    f"Argument < {name} > of non-null type < {arg_type} > "
                    "must not be null.",
                    locations=[argument_node.value.location],
                )
            elif argument_node and isinstance(
                argument_node.value, VariableNode
            ):
                raise GraphQLError(
                    f"Argument < {name} > of required type < {arg_type} > "
                    f"was provided the variable < ${variable_name} > which "
                    "was not provided a runtime value.",
                    locations=[argument_node.value.location],
                )
            else:
                raise GraphQLError(
                    f"Argument < {name} > of required type < {arg_type} > was "
                    "not provided."
                )
        elif has_value:
            if isinstance(argument_node.value, NullValueNode):
                coerced_values[name] = None
            elif isinstance(argument_node.value, VariableNode):
                variable_name = argument_node.value.name.value
                coerced_values[name] = variable_values[variable_name]
            else:
                value_node = argument_node.value
                coerced_value = value_from_ast(
                    value_node, arg_type, variable_values
                )
                if is_invalid_value(coerced_value):
                    raise GraphQLError(
                        f"Argument < {name} > has invalid value "
                        f"< {value_node} >."
                    )
                coerced_values[name] = coerced_value
    return coerced_values


async def variable_definition_coercer(
    executable_variable_definition: "ExecutableVariableDefinition",
    raw_variable_values: Dict[str, Any],
    input_coercer: Optional[Callable],
) -> Union["CoercionResult", "UNDEFINED_VALUE"]:
    """
    TODO:
    :param executable_variable_definition: TODO:
    :param raw_variable_values: TODO:
    :param input_coercer: TODO:
    :type executable_variable_definition: TODO:
    :type raw_variable_values: TODO:
    :type input_coercer: TODO:
    :return: TODO:
    :rtype: TODO:
    """
    var_name = executable_variable_definition.name
    var_type = executable_variable_definition.graphql_type

    if not is_input_type(var_type):
        definition_type = executable_variable_definition.definition.type
        return CoercionResult(
            errors=[
                graphql_error_from_nodes(
                    f"Variable < ${var_name} > expected value of type "
                    f"< {definition_type} > which cannot be used as "
                    "an input type.",
                    nodes=definition_type,
                )
            ]
        )

    has_value = var_name in raw_variable_values
    value = raw_variable_values.get(var_name, UNDEFINED_VALUE)
    default_value = executable_variable_definition.default_value

    if not has_value and default_value is not UNDEFINED_VALUE:
        return CoercionResult(value=default_value)

    if (not has_value or value is None) and is_non_null_type(var_type):
        return CoercionResult(
            errors=[
                graphql_error_from_nodes(
                    (
                        f"Variable < ${var_name} > of non-null type "
                        f"< {var_type} > must not be null."
                    )
                    if has_value
                    else (
                        f"Variable < ${var_name} > of required type "
                        f"< {var_type} > was not provided."
                    ),
                    nodes=executable_variable_definition.definition,
                )
            ]
        )

    if has_value:
        coerced_value, coerce_errors = await input_coercer(value)
        if coerce_errors:
            for coerce_error in coerce_errors:
                coerce_error.message = (  # TODO: incase of error raised in directives, message will be added? Is it ok?
                    f"Variable < ${var_name} > got invalid value "
                    f"< {value} >; {coerce_error.message}"
                )
            return CoercionResult(errors=coerce_errors)
        return CoercionResult(value=coerced_value)
    return UNDEFINED_VALUE


async def coerce_variable_definitions(
    executable_variable_definitions: List["ExecutableVariableDefinition"],
    raw_variable_values: Dict[str, Any],
) -> Tuple[Dict[str, Any], List["GraphQLError"]]:
    """
    TODO:
    :param executable_variable_definitions: TODO:
    :param raw_variable_values: TODO:
    :type executable_variable_definitions: TODO:
    :type raw_variable_values: TODO:
    :return: TODO:
    :rtype: TODO:
    """
    results = await asyncio.gather(
        *[
            executable_variable_definition.coercer(raw_variable_values)
            for executable_variable_definition in executable_variable_definitions
        ],
        return_exceptions=True,
    )

    coercion_errors: List["GraphQLError"] = []
    coerced_values: Dict[str, Any] = {}

    for executable_variable_definition, result in zip(
        executable_variable_definitions, results
    ):
        if result is UNDEFINED_VALUE:
            continue

        value, errors = result
        if errors:
            coercion_errors.extend(errors)
        else:
            coerced_values[executable_variable_definition.name] = value

    return coerced_values, coercion_errors
