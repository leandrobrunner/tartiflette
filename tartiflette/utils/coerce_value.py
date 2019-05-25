from collections import Iterable, Mapping
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Union

from tartiflette.constants import UNDEFINED_VALUE
from tartiflette.types.exceptions import GraphQLError
from tartiflette.types.exceptions.tartiflette import MultipleException
from tartiflette.types.helpers import wraps_with_directives
from tartiflette.types.helpers.definition import (
    get_wrapped_type,
    is_enum_type,
    is_input_object_type,
    is_list_type,
    is_non_null_type,
    is_scalar_type,
    is_wrapping_type,
)
from tartiflette.utils.coercer_way import CoercerWay
from tartiflette.utils.errors import is_coercible_exception
from tartiflette.utils.values import is_invalid_value


class Path:
    """
    Representations of the path traveled during the coercion.
    """

    __slots__ = ("prev", "key")

    def __init__(self, prev: Optional["Path"], key: Union[str, int]) -> None:
        """
        :param prev: the previous value of the path
        :param key: the current value of the path
        :type prev: Optional[Path]
        :type key: Union[str, int]
        """
        self.prev = prev
        self.key = key

    def __repr__(self) -> str:
        """
        Returns the representation of an Path instance.
        :return: the representation of an Path instance
        :rtype: str
        """
        return "Path(prev=%r, key=%r)" % (self.prev, self.key)

    def __str__(self) -> str:
        """
        Returns a human-readable representation of the full path.
        :return: a human-readable representation of the full path
        :rtype: str
        """
        path_str = ""
        current_path = self
        while current_path:
            path_str = (
                f".{current_path.key}"
                if isinstance(current_path.key, str)
                else f"[{current_path.key}]"
            ) + path_str
            current_path = current_path.prev
        return f"value{path_str}" if path_str else ""


class CoercionResult:
    """
    Represents the result of a coercion.
    """

    __slots__ = ("value", "errors")

    def __init__(
        self,
        value: Optional[Any] = None,
        errors: Optional[List["GraphQLError"]] = None,
    ) -> None:
        """
        :param value: the computed value
        :param errors: the errors encountered
        :type value: Optional[Any]
        :type errors: Optional[List[GraphQLError]]
        """
        # TODO: if errors `value` shouldn't it be "UNDEFINED_VALUE" instead?
        self.value = value if not errors else None
        self.errors = errors

    def __repr__(self) -> str:
        """
        Returns the representation of a CoercionResult instance.
        :return: the representation of a CoercionResult instance
        :rtype: str
        """
        return "CoercionResult(value=%r, errors=%r)" % (
            self.value,
            self.errors,
        )

    def __iter__(self) -> Iterable:
        """
        Returns an iterator over the computed value and errors encountered to
        allow unpacking the value like a tuple.
        :return: an iterator over the computed value and errors encountered
        :rtype: Iterable
        """
        yield from [self.value, self.errors]


def coercion_error(
    message: str,
    node: Optional["Node"] = None,
    path: Optional["Path"] = None,
    sub_message: Optional[str] = None,
    original_error: Optional[Exception] = None,
) -> "GraphQLError":
    """
    Returns a GraphQLError whose message is formatted according to the message,
    path, and sub-message filled in.
    :param message: the message of the error
    :param node: the AST node linked to the error
    :param path: the path where the error occurred
    :param sub_message: the sub-message to append
    :param original_error: the original raw exception
    :type message: str
    :type node: Optional[Node]
    :type path: Optional[Path]
    :type sub_message: Optional[str]
    :type original_error: Optional[Exception]
    :return: a GraphQLError
    :rtype: GraphQLError
    """
    return GraphQLError(
        message
        + (" at " + str(path) if path else "")
        + ("; " + sub_message if sub_message else "."),
        locations=[node.location] if node else None,
        path=None,
        original_error=original_error,
    )


async def scalar_coercer(
    scalar: "GraphQLScalarType",
    node: "Node",
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of a scalar.
    :param scalar: the GraphQLScalarType instance of the scalar
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param path: the path traveled until this coercer
    :type scalar: GraphQLScalarType
    :type node: Node
    :type value: Any
    :type path: Optional[Path"]
    :return: the coercion result
    :rtype: CoercionResult
    """
    # pylint: disable=unused-argument
    if value is None:
        return CoercionResult(value=None)

    try:
        coerced_value = scalar.coerce_input(value)
        if is_invalid_value(coerced_value):
            return CoercionResult(
                errors=[
                    coercion_error(
                        f"Expected type < {scalar.name} >", node, path
                    )
                ]
            )
    except Exception as e:  # pylint: disable=broad-except
        return CoercionResult(
            errors=[
                coercion_error(
                    f"Expected type < {scalar.name} >",
                    node,
                    path,
                    sub_message=str(e),
                    original_error=e,
                )
            ]
        )
    return CoercionResult(value=coerced_value)


async def enum_coercer(
    enum: "GraphQLEnumType",
    node: "Node",
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of an enum.
    :param enum: the GraphQLEnumType instance of the enum
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param path: the path traveled until this coercer
    :type enum: GraphQLEnumType
    :type node: Node
    :type value: Any
    :type path: Optional[Path"]
    :return: the coercion result
    :rtype: CoercionResult
    """
    if value is None:
        return CoercionResult(value=None)

    try:
        enum_value = enum.get_enum_value(value)

        # TODO: Wait, That's Illegal
        kwargs["ctx"] = None
        kwargs["argument_definition"] = None
        kwargs["info"] = None

        return CoercionResult(
            value=(
                await enum_value.directives[
                    CoercerWay.INPUT
                ](  # TODO: do better
                    value, *args, **kwargs
                )
            )
        )
        # return CoercionResult(value=enum.get_value(value))
    except KeyError:
        # TODO: try to compute a suggestion list of valid values depending
        # on the invalid value sent and returns it as error sub message
        return CoercionResult(
            errors=[
                coercion_error(f"Expected type < {enum.name} >", node, path)
            ]
        )


async def input_object_coercer(
    input_object: "GraphQLInputObjectType",
    input_field_coercers: Dict[str, Callable],
    node: "Node",
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of an input object.
    :param input_object: the GraphQLInputObjectType instance of the input
    object
    :param input_field_coercers: a dictionary of pre-computed coercer for each
    fields
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param path: the path traveled until this coercer
    :type input_object: GraphQLInputObjectType
    :type input_field_coercers: Dict[str, Callable]
    :type node: Node
    :type value: Any
    :type path: Optional[Path"]
    :return: the coercion result
    :rtype: CoercionResult
    """
    # pylint: disable=unused-argument,too-many-locals
    if value is None:
        return CoercionResult(value=None)

    if not isinstance(value, Mapping):
        return CoercionResult(
            errors=[
                coercion_error(
                    f"Expected type < {input_object.name} > to be an object",
                    node,
                    path,
                )
            ]
        )

    errors = []
    coerced_values = {}
    fields = input_object.arguments

    for field_name, field in fields.items():
        field_value = value.get(field_name, UNDEFINED_VALUE)
        if is_invalid_value(field_value):
            # TODO: at schema build we should use UNDEFINED_VALUE for
            # `default_value` attribute of a field to know if a field has
            # a defined default value (since default value could be `None`)
            # once done, we should check for `UNDEFINED_VALUE` here.
            if field.default_value is not None:
                coerced_values[field_name] = field.default_value
            # TODO: check if `gql_type` is the correct attr to call here
            elif is_non_null_type(field.gql_type):
                errors.append(
                    coercion_error(
                        f"Field < {Path(path, field_name)} > of required type "
                        f"< {field.gql_type} > was not provided",
                        node,
                    )
                )
        else:
            coerced_field_value, coerced_field_errors = await input_field_coercers[
                field_name
            ](
                node, field_value, path=Path(path, field_name)
            )
            if coerced_field_errors:
                errors.extend(coerced_field_errors)
            elif not errors:
                coerced_values[field_name] = coerced_field_value

    for field_name in value:
        if field_name not in fields:
            # TODO: try to compute a suggestion list of valid fields
            # depending on the invalid field name returns it as
            # error sub message
            errors.append(
                coercion_error(
                    f"Field < {field_name} > is not defined by type "
                    f"< {input_object.name} >.",
                    node,
                    path,
                )
            )

    return CoercionResult(value=coerced_values, errors=errors)


async def list_coercer(
    inner_coercer: Callable,
    node: "Node",
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of a list.
    :param inner_coercer: the pre-computed coercer to use on each value in the
    list
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param path: the path traveled until this coercer
    :type inner_coercer: Callable
    :type node: Node
    :type value: Any
    :type path: Optional[Path"]
    :return: the coercion result
    :rtype: CoercionResult
    """
    # pylint: disable=unused-argument,too-many-locals
    if value is None:
        return CoercionResult(value=None)

    if isinstance(value, Iterable):  # TODO: str are iterable so?...
        errors = []
        coerced_values = []
        # TODO: maybe should we gather them?
        for index, item_value in enumerate(value):
            coerced_value, coerce_errors = await inner_coercer(
                node, item_value, path=Path(path, index)
            )
            if coerce_errors:
                errors.extend(coerce_errors)
            elif not errors:
                coerced_values.append(coerced_value)
        return CoercionResult(value=coerced_values, errors=errors)

    coerced_item_value, coerced_item_errors = await inner_coercer(
        node, value, path=path
    )
    return CoercionResult(
        value=[coerced_item_value], errors=coerced_item_errors
    )


async def non_null_coercer(
    schema_type: "GraphQLType",
    inner_coercer: Callable,
    node: "Node",
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Computes the value of a list.
    :param schema_type: the schema type of the expected value
    :param inner_coercer: the pre-computed coercer to use on each value in the
    list
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param path: the path traveled until this coercer
    :type schema_type: GraphQLType
    :type inner_coercer: Callable
    :type node: Node
    :type value: Any
    :type path: Optional[Path"]
    :return: the coercion result
    :rtype: CoercionResult
    """
    # pylint: disable=unused-argument
    if value is None:
        return CoercionResult(
            errors=[
                coercion_error(
                    f"Expected non-nullable type < {schema_type} > not to be null",
                    node,
                    path,
                )
            ]
        )
    return await inner_coercer(node, value, path=path)


async def input_directive_coercer(
    directives: Callable,
    coercers: Callable,
    node: "Node",
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    Executes the directives on the coerced value.
    :param directives: the directives to execute
    :param coercers: the coercers to execute to get the coerced value
    :param node: the AST node to treat
    :param value: the raw value to compute
    :param path: the path traveled until this coercer
    :type directives: Callable
    :type coercers: Callable
    :type node: Node
    :type value: Any
    :type path: Optional[Path"]
    :return: the coercion result
    :rtype: CoercionResult
    """
    result = await coercers(node, value, *args, path=path, **kwargs)

    if result is UNDEFINED_VALUE:
        return UNDEFINED_VALUE

    value, errors = result
    if errors:
        return result

    # TODO: Wait, That's Illegal
    kwargs["ctx"] = None
    kwargs["argument_definition"] = None
    kwargs["info"] = None

    try:
        return CoercionResult(value=await directives(value, *args, **kwargs))
    except Exception as raw_exception:  # pylint: disable=broad-except
        return CoercionResult(
            errors=[
                coercion_error(
                    str(raw_exception),
                    node,
                    path,
                    original_error=(
                        raw_exception
                        if not is_coercible_exception(raw_exception)
                        else None
                    ),
                )
                for raw_exception in (
                    raw_exception.exceptions
                    if isinstance(raw_exception, MultipleException)
                    else [raw_exception]
                )
            ]
        )


def get_variable_definition_coercer(
    schema_type: "GraphQLType",
    directives_definition: Optional[List[Dict[str, Any]]] = None,
) -> Callable:
    """
    Computes and returns the coercer to use for the filled in schema type.
    :param schema_type: the schema type for which compute the coercer
    :param directives_definition: the directives with which to wrap the coercer
    :type schema_type: GraphQLType
    :type directives_definition: Optional[List[Dict[str, Any]]]
    :return: the computed coercer wrap with directives if defined
    :rtype: Callable
    """
    wrapped_type = get_wrapped_type(schema_type)

    wrapped_type_directives = getattr(
        wrapped_type, "directives_definition", None
    )
    directives_definition = (
        wrapped_type_directives
        if directives_definition is None
        else directives_definition + wrapped_type_directives
    )

    if is_scalar_type(wrapped_type):
        coercer = partial(scalar_coercer, wrapped_type)
    elif is_enum_type(wrapped_type):
        coercer = partial(enum_coercer, wrapped_type)
    elif is_input_object_type(wrapped_type):
        coercer = partial(
            input_object_coercer,
            wrapped_type,
            {
                name: get_variable_definition_coercer(
                    argument.graphql_type, argument.directives_definition
                )
                for name, argument in wrapped_type.arguments.items()
            },
        )
    else:
        coercer = lambda *args, **kwargs: None  # Not an InputType anyway...

    inner_type = schema_type
    wrapper_coercers = []
    while is_wrapping_type(inner_type):
        if is_list_type(inner_type):
            wrapper_coercers.append(list_coercer)
        elif is_non_null_type(inner_type):
            wrapper_coercers.append(partial(non_null_coercer, inner_type))
        inner_type = inner_type.wrapped_type

    for wrapper_coercer in reversed(wrapper_coercers):
        coercer = partial(wrapper_coercer, coercer)

    if directives_definition:
        directives = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_post_input_coercion",
        )
        if directives:
            coercer = partial(input_directive_coercer, directives, coercer)

    return coercer
