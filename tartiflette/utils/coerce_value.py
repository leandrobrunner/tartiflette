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
from tartiflette.utils.errors import is_coercible_exception, to_graphql_error
from tartiflette.utils.values import is_invalid_value


class Path:
    """
    TODO:
    """

    __slots__ = ("prev", "key")

    def __init__(self, prev: Optional["Path"], key: Union[str, int]) -> None:
        """
        :param prev: TODO:
        :param key: TODO:
        :type prev: TODO:
        :type key: TODO:
        """
        self.prev = prev
        self.key = key

    def __repr__(self) -> str:
        """
        TODO:
        :return: TODO:
        :rtype: TODO:
        """
        return "Path(prev=%r, key=%r)" % (self.prev, self.key)

    def __str__(self) -> str:
        """
        TODO:
        :return: TODO:
        :rtype: TODO:
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
    TODO:
    """

    __slots__ = ("value", "errors")

    def __init__(
        self,
        value: Optional[Any] = None,
        errors: Optional[List["GraphQLError"]] = None,
    ) -> None:
        """
        :param value: TODO:
        :param errors: TODO:
        :type value: TODO:
        :type errors: TODO:
        """
        # TODO: if errors `value` shouldn't it be "UNDEFINED_VALUE" instead?
        self.value = value if not errors else None
        self.errors = errors

    def __repr__(self) -> str:
        """
        TODO:
        :return: TODO:
        :rtype: TODO:
        """
        return "CoercionResult(value=%r, errors=%r)" % (
            self.value,
            self.errors,
        )

    def __iter__(self) -> Iterable:
        """
        TODO:
        :return: TODO:
        :rtype: TODO:
        """
        yield from [self.value, self.errors]


def coercion_error(
    message, node=None, path=None, sub_message=None, original_error=None
):
    """
    TODO:
    :param message: TODO:
    :param node: TODO:
    :param path: TODO:
    :param sub_message: TODO:
    :param original_error: TODO:
    :type message: TODO:
    :type node: TODO:
    :type path: TODO:
    :type sub_message: TODO:
    :type original_error: TODO:
    :return: TODO:
    :rtype: TODO:
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
    node: Optional["Node"],
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    TODO:
    :param scalar: TODO:
    :param node: TODO:
    :param path: TODO:
    :param value: TODO:
    :param args: TODO:
    :param kwargs: TODO:
    :type scalar: TODO:
    :type node: TODO:
    :type path: TODO:
    :type value: TODO:
    :type args: TODO:
    :type kwargs: TODO:
    :return: TODO:
    :rtype: TODO:
    """
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
    except Exception as e:
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
    node: Optional["Node"],
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    TODO:
    :param enum: TODO:
    :param node: TODO:
    :param path: TODO:
    :param value: TODO:
    :param args: TODO:
    :param kwargs: TODO:
    :type enum: TODO:
    :type node: TODO:
    :type path: TODO:
    :type value: TODO:
    :type args: TODO:
    :type kwargs: TODO:
    :return: TODO:
    :rtype: TODO:
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
    node: Optional["Node"],
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    TODO:
    :param input_object: TODO:
    :param input_field_coercers: TODO:
    :param node: TODO:
    :param path: TODO:
    :param value: TODO:
    :type input_object: TODO:
    :type input_field_coercers: TODO:
    :type node: TODO:
    :type path: TODO:
    :type value: TODO:
    :return: TODO:
    :rtype: TODO:
    """
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
    node: Optional["Node"],
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    TODO:
    :param inner_coercer: TODO:
    :param node: TODO:
    :param path: TODO:
    :param value: TODO:
    :param args: TODO:
    :param kwargs: TODO:
    :type inner_coercer: TODO:
    :type node: TODO:
    :type path: TODO:
    :type value: TODO:
    :type args: TODO:
    :type kwargs: TODO:
    :return: TODO:
    :rtype: TODO:
    """
    if value is None:
        return CoercionResult(value=None)

    if isinstance(value, Iterable):  # TODO: str are iterable so?...
        errors = []
        coerced_values = []
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
    node: Optional["Node"],
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
    """
    TODO:
    :param schema_type: TODO:
    :param inner_coercer: TODO:
    :param node: TODO:
    :param path: TODO:
    :param value: TODO:
    :param args: TODO:
    :param kwargs: TODO:
    :type schema_type: TODO:
    :type inner_coercer: TODO:
    :type node: TODO:
    :type path: TODO:
    :type value: TODO:
    :type args: TODO:
    :type kwargs: TODO:
    :return: TODO:
    :rtype: TODO:
    """
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
    directives,
    coercers,
    # schema_type: "GraphQLType",
    # inner_coercer: Callable,
    node: Optional["Node"],
    value: Any,
    *args,
    path: Optional["Path"] = None,
    **kwargs,
) -> "CoercionResult":
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
    except Exception as raw_exception:
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
    TODO:
    :param schema_type: TODO:
    :param directives_definition: TODO:
    :type schema_type: TODO:
    :type directives_definition: TODO:
    :return: TODO:
    :rtype: TODO:
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

    for wrapper_coercer in wrapper_coercers[::-1]:
        coercer = partial(wrapper_coercer, coercer)

    if directives_definition:
        directives = wraps_with_directives(
            directives_definition=directives_definition,
            directive_hook="on_post_input_coercion",
        )
        if directives:
            coercer = partial(input_directive_coercer, directives, coercer)

    return coercer
