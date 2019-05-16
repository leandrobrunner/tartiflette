from collections import Callable
from typing import Any, Dict, List, Optional


def build_response(
    error_coercer: Callable,
    data: Optional[Dict[str, Any]] = None,
    errors: Optional[List["GraphQLError"]] = None,
) -> Dict[str, Any]:
    """
    TODO:
    :param error_coercer: TODO:
    :param data: TODO:
    :param errors: TODO:
    :type error_coercer: TODO:
    :type data: TODO:
    :type errors: TODO:
    :return: TODO:
    :rtype: TODO:
    """
    coerced_errors = (
        [error_coercer(error) for error in errors] if errors else None
    )
    if coerced_errors:
        return {"data": data, "errors": coerced_errors}
    return {"data": data}
