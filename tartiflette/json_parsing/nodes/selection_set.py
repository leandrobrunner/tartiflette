import asyncio
import collections

from typing import Any, Dict, List, Optional, Set, Union

from tartiflette.error.base import GraphQLError
from tartiflette.executors.types import Info
from tartiflette.json_parsing.nodes import (
    FieldNode,
    FragmentSpreadNode,
    InlineFragmentNode,
)
from tartiflette.json_parsing.nodes.base import Node
from tartiflette.validations.validators import (
    is_abstract_type,
    is_leaf_type,
    is_list_type,
    is_non_null_type,
    is_object_type,
)


def should_include_node(
    execution_context: "ExecutionContext",
    node: Union["FieldNode", "InlineFragmentNode", "FragmentSpreadNode"],
) -> bool:
    # TODO: implement the method in charge of checking if `if` or `include`
    #  directive exists and if condition result is True.
    return True


def does_fragment_condition_match(
    execution_context: "ExecutionContext",
    fragment_node: "FragmentDefinitionNode",
    object_type: "GraphQLType",
) -> bool:
    from tartiflette.execution.values import type_from_ast

    fragment_node_type_condition = fragment_node.type_condition
    if not fragment_node_type_condition:
        return True

    fragment_type: "GraphQLType" = type_from_ast(
        execution_context.schema, fragment_node_type_condition
    )
    if fragment_type == object_type:
        return True

    return is_abstract_type(fragment_type) and fragment_type.is_possible_type(
        object_type
    )


class SelectionSetNode(Node):
    KIND = "SelectionSet"

    def __init__(
        self,
        selections: List[
            Union["FieldNode", "FragmentSpreadNode", "InlineFragmentNode"]
        ],
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._selections = selections

    @property
    def selections(
        self
    ) -> List[Union["FieldNode", "FragmentSpreadNode", "InlineFragmentNode"]]:
        return self._selections

    def collect_fields(
        self,
        execution_context: "ExecutionContext",
        parent_type: "GraphQLType",
        fields: Optional[Dict[str, "FieldNode"]] = None,
        visited_fragments: Optional[Set[str]] = None,
    ):
        if fields is None:
            fields = {}

        if visited_fragments is None:
            visited_fragments = set()

        for selection in self._selections:
            if not should_include_node(execution_context, selection):
                continue

            if isinstance(selection, FieldNode):
                fields.setdefault(selection.response_key, []).append(selection)
            elif isinstance(selection, InlineFragmentNode):
                if not does_fragment_condition_match(
                    execution_context, selection, parent_type
                ):
                    continue

                selection.selection_set.collect_fields(
                    execution_context, parent_type, fields, visited_fragments
                )
            elif isinstance(selection, FragmentSpreadNode):
                fragment_name = selection.name.value
                if fragment_name in visited_fragments:
                    continue

                visited_fragments.add(fragment_name)

                fragment_definition_node = execution_context.fragments.get(
                    fragment_name
                )

                if (
                    not fragment_definition_node
                    or not does_fragment_condition_match(
                        execution_context,
                        fragment_definition_node,
                        parent_type,
                    )
                ):
                    continue

                fragment_definition_node.selection_set.collect_fields(
                    execution_context, parent_type, fields, visited_fragments
                )

        return fields

    async def __call__(
        self,
        execution_context: "ExecutionContext",
        parent_type: "GraphQLType",
        parent_value: Any,
        allow_parallelization: bool = True,
    ) -> Dict[str, Any]:
        selection_set_fields = self.collect_fields(
            execution_context, parent_type
        )

        print(">> SelectionSet.__call__", {"fields": selection_set_fields})

        results: Dict[str, Any] = {}

        if not allow_parallelization:
            for response_key, field_nodes in selection_set_fields.items():
                results[response_key] = await resolve_field_value(
                    execution_context, parent_type, parent_value, field_nodes
                )
        else:
            parallelized_results = await asyncio.gather(
                *[
                    resolve_field_value(
                        execution_context,
                        parent_type,
                        parent_value,
                        field_nodes,
                    )
                    for field_nodes in selection_set_fields.values()
                ],
                return_exceptions=False,
            )
            for response_key, parallelized_results in zip(
                selection_set_fields.keys(), parallelized_results
            ):
                results[response_key] = parallelized_results

        return results

        # if not allow_parallelization:
        #     for field_node

        return results


def coerce_argument_values(
    field_type: "GraphQLField",
    field_node: "FieldNode",
    variable_values: Dict[str, Any],
) -> Dict[str, Any]:
    # TODO:
    # https://facebook.github.io/graphql/June2018/#CoerceArgumentValues()
    # https://github.com/graphql/graphql-js/blob/master/src/execution/values.js
    argument_definitions = field_type.arguments
    node_arguments = field_node.arguments

    if not argument_definitions or not node_arguments:
        return {}

    node_arguments_map = {
        argument.name.value: argument for argument in node_arguments
    }

    coerced_values = {}
    for argument_name, argument_definition in argument_definitions.items():
        value_from_node = node_arguments_map.get(argument_name)
        if value_from_node:
            value_from_node = value_from_node.value

        value = value_from_node

        if value is None:
            value = argument_definition.default_value

        if value is not None:
            coerced_values[argument_name] = value

    return coerced_values


async def resolve_field_value(
    execution_context: "ExecutionContext",
    parent_type: "GraphQLType",
    parent_value: Any,
    field_nodes: List["FieldNode"],
) -> Any:
    field_node = field_nodes[0]
    field_name = field_node.name.value

    field_type: "GraphQLField" = execution_context.schema.get_field_by_name(
        str(parent_type) + "." + field_name
    )

    info = Info(
        query_field=field_node,
        schema_field=field_type,
        schema=execution_context.schema,
        path=[],  # correct path here
        location=field_node.location,
        execution_ctx=execution_context,
    )

    _, coerced_value = await field_type.resolver(
        parent_value,
        coerce_argument_values(
            field_type, field_node, execution_context.variable_values
        ),
        execution_context.context_value,
        info,
    )

    return complete_value(
        execution_context, parent_type, field_nodes, info, coerced_value
    )


def complete_value(
    execution_context: "ExecutionContext",
    return_type: "GraphQLType",
    field_nodes: List["FieldNode"],
    info: "Info",
    result: Any,
):
    if is_non_null_type(return_type):
        completed_value = complete_value(
            execution_context, return_type.gql_type, field_nodes, info, result
        )
        if completed_value is None:
            raise GraphQLError(
                "Cannot return null for non-nullable field < %s.%s >."
                % (str(return_type), str(field_nodes[0].name.value))
            )
        return completed_value

    if result is None:
        return None

    if is_list_type(return_type):
        return complete_list_value(
            execution_context, return_type, field_nodes, info, result
        )

    if is_leaf_type(return_type):
        return complete_leaf_value(return_type, result)

    if is_abstract_type(return_type):
        return complete_abastract_value(
            execution_context, return_type, field_nodes, info, result
        )

    if is_object_type(return_type):
        return complete_object_value(
            execution_context, return_type, field_nodes, info, result
        )

    if is_abstract_type(return_type):
        return complete_object_value(
            execution_context, return_type, field_nodes, info, result
        )


def complete_list_value(
    execution_context: "ExecutionContext",
    return_type: "GraphQLType",
    field_nodes: List["FieldNode"],
    info: "Info",
    result: Any,
):
    if not isinstance(result, collections.Iterable):
        raise GraphQLError(
            "Expected iterable, but did not find one for field < %s.%s >."
            % (str(return_type), str(field_nodes[0].name.value))
        )

    item_type = return_type.gql_type
    return [
        complete_value(execution_context, item_type, field_nodes, info, item)
        for item in result
    ]


def is_invalid(result):
    # TODO: implement this function
    return True


def complete_leaf_value(return_type: "GraphQLType", result: Any):
    print(
        ">> complete_leaf_value",
        {"return_type": return_type, "type(return_type)": type(return_type)},
    )

    try:
        serialized_result = return_type.coerce_output(result)
    except AttributeError:
        raise GraphQLError("Missing serialize method on type.")

    if is_invalid(serialized_result):
        raise GraphQLError(
            "Expected a value of type < %s > but received: < %s >."
            % (type(return_type), type(result))
        )

    return serialized_result


def complete_object_value(
    execution_context: "ExecutionContext",
    return_type: "GraphQLType",
    field_nodes: List["FieldNode"],
    info: "Info",
    result: Any,
):
    if not isinstance(result, collections.Iterable):
        raise GraphQLError(
            "Expected iterable, but did not find one for field < %s.%s >."
            % (str(return_type), str(field_nodes[0].name.value))
        )

    item_type = return_type.gql_type
    return [
        complete_value(execution_context, item_type, field_nodes, info, item)
        for item in result
    ]


def complete_abastract_value(
    execution_context: "ExecutionContext",
    return_type: "GraphQLType",
    field_nodes: List["FieldNode"],
    info: "Info",
    result: Any,
):
    # TODO: implement it
    pass
