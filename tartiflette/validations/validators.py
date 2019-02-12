from tartiflette.types.enum import GraphQLEnumType
from tartiflette.types.input_object import GraphQLInputObjectType
from tartiflette.types.interface import GraphQLInterfaceType
from tartiflette.types.list import GraphQLList
from tartiflette.types.non_null import GraphQLNonNull
from tartiflette.types.object import GraphQLObjectType
from tartiflette.types.scalar import GraphQLScalarType
from tartiflette.types.union import GraphQLUnionType


def is_list_type(node_type):
    return isinstance(node_type, GraphQLList)


def is_non_null_type(node_type):
    return isinstance(node_type, GraphQLNonNull)


def is_scalar_type(node_type):
    return isinstance(node_type, GraphQLScalarType)


def is_enum_type(node_type):
    return isinstance(node_type, GraphQLEnumType)


def is_input_node_type(node_type):
    return isinstance(node_type, GraphQLInputObjectType)


def is_wrapping_type(node_type):
    return isinstance(node_type, (GraphQLList, GraphQLNonNull))


def is_leaf_type(node_type):
    return isinstance(node_type, (GraphQLScalarType, GraphQLEnumType))


def get_named_type(node_type):
    named_type = node_type
    while isinstance(named_type, (GraphQLList, GraphQLNonNull)):
        named_type = named_type.gql_type
    return named_type


def is_input_type(node_type):
    return isinstance(
        get_named_type(node_type),
        (GraphQLScalarType, GraphQLEnumType, GraphQLInputObjectType),
    )


def is_abstract_type(node_type) -> bool:
    return isinstance(node_type, (GraphQLInterfaceType, GraphQLUnionType))


def is_object_type(node_type) -> bool:
    return isinstance(node_type, GraphQLObjectType)
