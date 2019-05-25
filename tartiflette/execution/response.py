from collections import Callable
from typing import Any, Dict, List, Optional


def build_response(
    error_coercer: Callable,
    data: Optional[Dict[str, Any]] = None,
    errors: Optional[List["GraphQLError"]] = None,
) -> Dict[str, Any]:
    """
    Returns and formats the data and errors into a proper GraphQL response.
    :param error_coercer: callable in charge of transforming a couple
    Exception/error into an error dictionary
    :param data: the data from fields execution
    :param errors: the errors encountered during the request execution
    :type error_coercer: Callable
    :type data: Optional[Dict[str, Any]]
    :type errors: Optional[List[GraphQLError]]
    :return: a GraphQL response
    :rtype: Dict[str, Any]
    """
    coerced_errors = (
        [error_coercer(error) for error in errors] if errors else None
    )
    if coerced_errors:
        return {"data": data, "errors": coerced_errors}
    return {"data": data}
