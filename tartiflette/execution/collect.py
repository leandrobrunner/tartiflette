from functools import lru_cache, partial
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from tartiflette.execution.nodes.field import ExecutableFieldNode
from tartiflette.execution.nodes.variable_definition import (
    variable_definition_node_to_executable,
)
from tartiflette.execution.values import get_argument_values
from tartiflette.language.ast import (
    FieldNode,
    FragmentSpreadNode,
    InlineFragmentNode,
)
from tartiflette.language.parsers.libgraphqlparser import parse_to_document
from tartiflette.types.exceptions import GraphQLError
from tartiflette.types.exceptions.tartiflette import SkipCollection
from tartiflette.types.helpers import (
    reduce_type,
    transform_directive,
    wraps_with_directives,
)
from tartiflette.types.helpers.definition import is_abstract_type
from tartiflette.utils.arguments import coerce_arguments
from tartiflette.utils.errors import to_graphql_error
from tartiflette.utils.type_from_ast import schema_type_from_ast

__all__ = ["collect_executables"]


@lru_cache(maxsize=1024)
def parse_and_validate_query(
    query: Union[str, bytes]
) -> Tuple[Optional["DocumentNode"], Optional[List["GraphQLError"]]]:
    """
    Analyzes & validates a query by converting it to a DocumentNode.
    :param query: the GraphQL request / query as UTF8-encoded string
    :type query: Union[str, bytes]
    :return: a DocumentNode representing the query
    :rtype: Tuple[Optional[DocumentNode], Optional[List[GraphQLError]]]
    """
    try:
        document: "DocumentNode" = parse_to_document(query)
    except GraphQLError as e:
        return None, [e]
    except Exception as e:  # pylint: disable=broad-except
        return (
            None,
            [to_graphql_error(e, message="Server encountered an error.")],
        )
    # TODO: implements function which validate a document against rules
    # errors = validate_document(document)
    # if errors:
    #     return None, errors
    return document, None


def _does_fragment_condition_match(
    schema: "GraphQLSchema",
    fragment_definition: Union["FragmentDefinitionNode", "InlineFragmentNode"],
    graphql_type: "GraphQLType",
) -> bool:
    """
    Determines if a AST node is applicable to the given GraphQLType.
    :param schema: the GraphQLSchema schema instance linked to the engine
    :param fragment_definition: AST node to check
    :param graphql_type: GraphQLType that the AST node should comply with
    :type schema: GraphQLSchema:
    :type fragment_definition: Union[FragmentDefinitionNode, InlineFragmentNode]
    :type graphql_type: GraphQLType
    :return: whether or not the AST node is applicable to the given GraphQLType
    :rtype: bool
    """
    type_condition_node = fragment_definition.type_condition
    if not type_condition_node:
        return True

    conditional_type = schema_type_from_ast(schema, type_condition_node)
    if conditional_type is graphql_type:
        return True

    return is_abstract_type(graphql_type) and graphql_type.is_possible_types(
        conditional_type
    )


def _surround_with_collection_directives(
    func: Callable, directives: List[Dict[str, Any]]
) -> Callable:
    """
    Wraps the function with the provided directives.
    :param func: the function to wrap
    :param directives: the directives to wrap the function with
    :type func: Callable
    :type directives: List[Dict[str, Any]]
    :return: the wrapped function
    :rtype: Callable
    """
    for directive in reversed(directives):
        func = partial(directive["callable"], directive["args"], func)
    return func


async def _collect_directive(
    selection: Union["FieldNode", "FragmentSpreadNode", "InlineFragmentNode"]
) -> Union["FieldNode", "FragmentSpreadNode", "InlineFragmentNode"]:
    """
    An utility function which returns the selection AST node filled in and is
    intended to be decorated by directives.
    :param selection: the selection AST node filled in
    :type selection: Union[FieldNode, FragmentSpreadNode, InlineFragmentNode]
    :return: the selection AST node filled in
    :rtype: Union[FieldNode, FragmentSpreadNode, InlineFragmentNode]
    """
    return selection


async def _should_include_node(
    execution_context: "ExecutionContext",
    selection: Union["FieldNode", "FragmentSpreadNode", "InlineFragmentNode"],
    path: Optional[List[str]],
) -> bool:
    """
    Determines if a selection AST node should be included based on the
     `on_***_collection` directive hooks (linked to the @include and @skip
     directives).
    :param execution_context: the instance of the global execution context
    :param selection: the selection AST node to check
    :param path: the path linked to the selection AST node
    :type execution_context: ExecutionContext
    :type selection: Union[FieldNode, FragmentSpreadNode, InlineFragmentNode]
    :type path: Optional[List[str]]
    :return: whether or not the selection AST node should be include
    :rtype: bool
    """
    if not selection.directives:
        return True

    computed_directives = []
    for directive_node in selection.directives:
        try:
            directive = execution_context.schema.find_directive(
                directive_node.name.value
            )
            directive_dict = transform_directive(directive)
            directive_dict["args"] = await coerce_arguments(
                directive.arguments,
                get_argument_values(
                    directive.arguments,
                    directive_node,
                    execution_context.variable_values,
                ),
                execution_context.context,
                None,  # TODO: should be a "Info" instance
            )
        except Exception as e:  # pylint: disable=broad-except
            execution_context.add_error(
                e, path=path, locations=[directive_node.location]
            )
            return False

    directive_hook = (
        "on_field_collection"
        if isinstance(selection, FieldNode)
        else (
            "on_fragment_spread_collection"
            if isinstance(selection, FragmentSpreadNode)
            else "on_inline_fragment_collection"
        )
    )

    try:
        await wraps_with_directives(computed_directives, directive_hook)(
            selection
        )
    except SkipCollection:
        return False
    except Exception as e:  # pylint: disable=broad-except
        execution_context.add_error(
            e, path=path, locations=[selection.location]
        )
        return False
    return True


async def collect_executables(
    execution_context: "ExecutionContext",
    runtime_type: "GraphQLObjectType",
    selection_set: "SelectionSetNode",
    fields: Optional[Dict[str, "ExecutableFieldNode"]] = None,
    visited_fragments: Optional[Set[str]] = None,
    type_condition: Optional[str] = None,
    path: Optional[List[str]] = None,
    parent: Optional["ExecutableFieldNode"] = None,
) -> Dict[str, "ExecutableFieldNode"]:
    """
    Go recursively through all selection sets to collect all the fields to
    execute.
    :param execution_context: the instance of the global execution context
    :param runtime_type: the GraphQLObjectType linked to the selection set
    :param selection_set: the selection set to look over
    :param fields: a dictionary containing the collected fields
    :param visited_fragments: a set containing the names of the fragments
    already treated
    :param type_condition: the type condition liked to the selection set
    :param path: the path linked to the selection set
    :param parent: the parent field of the selection set
    :type execution_context: ExecutionContext
    :type runtime_type: GraphQLObjectType
    :type selection_set: SelectionSetNode
    :type fields: Optional[Dict[str, ExecutableFieldNode]]
    :type visited_fragments: Optional[Set[str]]
    :type type_condition: Optional[str]
    :type path: Optional[List[str]]
    :type parent: Optional[ExecutableFieldNode]
    :return: a dictionary containing the collected fields
    :rtype: Dict[str, ExecutableFieldNode]
    """
    # pylint: disable=too-many-locals
    if fields is None:
        fields: Dict[str, "ExecutableFieldNode"] = {}

    if visited_fragments is None:
        visited_fragments: Set[str] = set()

    for selection in selection_set.selections:
        if not await _should_include_node(execution_context, selection, path):
            continue

        selection_path: List[str] = path if path is not None else []

        if isinstance(selection, FieldNode):
            response_key: str = (
                selection.alias.value
                if selection.alias
                else selection.name.value
            )

            # Computes field's path
            field_path: List[str] = selection_path + [response_key]

            parent_field_type = (
                execution_context.schema.find_type(type_condition)
                if type_condition
                else runtime_type
            )
            field_type_condition = str(parent_field_type)
            graphql_field = parent_field_type.find_field(selection.name.value)
            field_type = execution_context.schema.find_type(
                reduce_type(graphql_field.gql_type)
            )

            fields.setdefault(field_type_condition, {}).setdefault(
                response_key,
                ExecutableFieldNode(
                    name=response_key,
                    schema=execution_context.schema,
                    resolver=graphql_field.resolver,
                    subscribe=graphql_field.subscribe,
                    path=field_path,
                    type_condition=field_type_condition,
                    parent=parent,
                    arguments=selection.arguments,
                    directives=selection.directives,
                ),
            )

            # Adds `FieldNode` to `ExecutableFieldNode` to have all locations
            # and definitions into `Info` resolver object
            fields[field_type_condition][response_key].definitions.append(
                selection
            )

            # Collects selection set fields
            if selection.selection_set:
                await collect_executables(
                    execution_context,
                    field_type,
                    selection.selection_set,
                    fields=fields[field_type_condition][response_key].fields,
                    path=field_path,
                    parent=fields[field_type_condition][response_key],
                )
        elif isinstance(selection, InlineFragmentNode):
            if not _does_fragment_condition_match(
                execution_context.schema, selection, runtime_type
            ):
                continue

            await collect_executables(
                execution_context,
                runtime_type,
                selection.selection_set,
                fields=fields,
                visited_fragments=visited_fragments,
                type_condition=(
                    selection.type_condition.name.value
                    if selection.type_condition
                    else type_condition
                ),
                path=selection_path,
                parent=parent,
            )
        elif isinstance(selection, FragmentSpreadNode):
            fragment_name = selection.name.value
            if fragment_name in visited_fragments:
                continue

            visited_fragments.add(fragment_name)

            fragment_definition = execution_context.fragments.get(
                fragment_name
            )
            if not fragment_definition:
                continue

            if not _does_fragment_condition_match(
                execution_context.schema, fragment_definition, runtime_type
            ):
                continue

            await collect_executables(
                execution_context,
                runtime_type,
                fragment_definition.selection_set,
                fields=fields,
                visited_fragments=visited_fragments,
                type_condition=fragment_definition.type_condition.name.value,
                path=selection_path,
                parent=parent,
            )

    return fields


def collect_executable_variable_definitions(
    schema: "GraphQLSchema",
    variable_definition_nodes: List["VariableDefinitionNode"],
) -> List["ExecutableVariableDefinition"]:
    """
    Go recursively through all variable definition AST nodes to convert them as
    executable variable definition.
    :param schema: the GraphQLSchema schema instance linked to the engine
    :param variable_definitions: the list of variable definition AST to treat
    :type schema: GraphQLSchema
    :type variable_definitions: List[VariableDefinitionNode]
    :return: a list of executable variable definition
    :rtype: List[ExecutableVariableDefinition]
    """
    return [
        variable_definition_node_to_executable(
            schema, variable_definition_node
        )
        for variable_definition_node in variable_definition_nodes
    ]
