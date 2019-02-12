from typing import List


class ValidationContext:
    def __init__(self) -> None:
        self._errors: List["GraphQLError"] = []

    @property
    def errors(self) -> List["GraphQLError"]:
        return self._errors

    def add_error(self, error: "GraphQLError") -> None:
        self._errors.append(error)

    def error_as_graphql_response(self, data=None):
        result = {"errors": [index for index, _ in enumerate(self._errors)]}
        if data:
            result["data"] = data
        return result
