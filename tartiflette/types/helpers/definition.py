from tartiflette.types.enum import GraphQLEnumType
from tartiflette.types.input_object import GraphQLInputObjectType
from tartiflette.types.interface import GraphQLInterfaceType
from tartiflette.types.list import GraphQLList
from tartiflette.types.non_null import GraphQLNonNull
from tartiflette.types.object import GraphQLObjectType
from tartiflette.types.scalar import GraphQLScalarType
from tartiflette.types.union import GraphQLUnionType


def get_wrapped_type(schema_type: "GraphQLType") -> "GraphQLType":
    """
    Unwraps the schema type and to return the inner type.
    :param schema_type: schema type to unwrap
    :type schema_type: GraphQLType
    :return: the unwrapped inner schema type
    :rtype: GraphQLType
    """
    inner_type = schema_type
    while is_wrapping_type(inner_type):
        inner_type = inner_type.wrapped_type
    return inner_type


def is_scalar_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is a scalar type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is a scalar type.
    :rtype: bool
    """
    return isinstance(schema_type, GraphQLScalarType)


def is_enum_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is an enum type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is an enum type.
    :rtype: bool
    """
    return isinstance(schema_type, GraphQLEnumType)


def is_input_object_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is an input object type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is an input object type.
    :rtype: bool
    """
    return isinstance(schema_type, GraphQLInputObjectType)


def is_list_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is a list type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is a list type.
    :rtype: bool
    """
    return isinstance(schema_type, GraphQLList)


def is_non_null_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is a non null type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is a non null type.
    :rtype: bool
    """
    return isinstance(schema_type, GraphQLNonNull)


def is_wrapping_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is either a list or non null
    type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is either a list or non null
    type.
    :rtype: bool
    """
    return isinstance(schema_type, (GraphQLList, GraphQLNonNull))


def is_input_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is an input type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is an input type.
    :rtype: bool
    """
    return isinstance(
        schema_type,
        (GraphQLScalarType, GraphQLEnumType, GraphQLInputObjectType),
    ) or (
        is_wrapping_type(schema_type)
        and is_input_type(schema_type.wrapped_type)
    )


def is_abstract_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is an abstract type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is an abstract type.
    :rtype: bool
    """
    return isinstance(schema_type, (GraphQLInterfaceType, GraphQLUnionType))


def is_leaf_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is a leaf type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is a leaf type.
    :rtype: bool
    """
    return isinstance(schema_type, (GraphQLScalarType, GraphQLEnumType))


def is_object_type(schema_type: "GraphQLType") -> bool:
    """
    Determines whether or not the "GraphQLType" is an object type.
    :param schema_type: schema type to test
    :type schema_type: GraphQLType
    :return: whether or not the "GraphQLType" is an object type.
    :rtype: bool
    """
    return isinstance(schema_type, GraphQLObjectType)
