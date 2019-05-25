from typing import List, Optional, Union

from tartiflette.types.exceptions.tartiflette import GraphQLError


def is_coercible_exception(exception: Exception) -> bool:
    """
    Determines whether or not the exception is coercible.
    :param exception: exception to check
    :type exception: Any
    :return: whether or not the exception is coercible
    :rtype: bool
    """
    return hasattr(exception, "coerce_value") and callable(
        exception.coerce_value
    )


def to_graphql_error(
    raw_exception: Exception, message: Optional[str] = None
) -> Union["GraphQLError", Exception]:
    """
    Converts the raw exception into a GraphQLError if its not coercible or
    returns the raw exception if coercible.
    :param raw_exception: the raw exception to be treated
    :param message: message replacing the raw exception message when it's not
    coercible
    :type raw_exception: Exception
    :type message: Optional[str]
    :return: a coercible exception
    :rtype: Union["GraphQLError", Exception]
    """
    return (
        raw_exception
        if is_coercible_exception(raw_exception)
        else GraphQLError(
            message or str(raw_exception), original_error=raw_exception
        )
    )


def graphql_error_from_nodes(
    message: str, nodes: Optional[Union["Node", List["Node"]]] = None
) -> "GraphQLError":
    """
    Returns a GraphQLError linked to a list of AST nodes which make it possible
    to fill in the location of the error.
    :param message: error message
    :param nodes: AST nodes to link to the error
    :type message: str
    :type nodes: Optional[Union["Node", List["Node"]]]
    :return: a GraphQLError with locations
    :rtype: GraphQLError
    """
    if nodes is None:
        nodes = []

    if not isinstance(nodes, list):
        nodes = [nodes]

    return GraphQLError(message, locations=[node.location for node in nodes])
