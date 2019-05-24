import pytest

from tartiflette import Directive, Engine, Resolver, Scalar
from tartiflette.directive import CommonDirective
from tartiflette.scalar import ScalarString


@Resolver("Query.channelz", schema_name="test_input_directives")
@Resolver("Query.channels", schema_name="test_input_directives")
async def resolve_query_channelsz(parent, args, ctx, info):
    return []


@Resolver("Query.users", schema_name="test_input_directives")
async def resolve_query_users(parent, args, ctx, info):
    return None


@Directive("debug", schema_name="test_input_directives")
class DebugDirective(CommonDirective):
    @staticmethod
    async def on_argument_execution(
        directive_args, next_directive, argument_definition, args, ctx, info
    ):
        result = await next_directive(argument_definition, args, ctx, info)
        print("-> on_argument_execution", directive_args.get("message"), args)
        return result

    @staticmethod
    async def on_post_input_coercion(
        directive_args,
        next_directive,
        value,
        argument_definition,
        ctx,
        info: "Info",
    ):
        result = await next_directive(value, argument_definition, ctx, info)
        print("-> on_post_input_coercion", directive_args.get("message"))
        return result

    @staticmethod
    async def on_pre_output_coercion(
        directive_args, next_directive, value, field_definition, ctx, info
    ):
        result = await next_directive(value, field_definition, ctx, info)
        print("-> on_pre_output_coercion", directive_args.get("message"))
        return result


@Directive("error", schema_name="test_input_directives")
class ErrorDirective(CommonDirective):
    @staticmethod
    async def on_argument_execution(
        directive_args, next_directive, argument_definition, args, ctx, info
    ):
        print("-> on_argument_execution error")
        raise ValueError("on_argument_execution error")

    @staticmethod
    async def on_post_input_coercion(
        directive_args,
        next_directive,
        value,
        argument_definition,
        ctx,
        info: "Info",
    ):
        print("-> on_post_input_coercion error")
        raise ValueError("on_post_input_coercion error")

    @staticmethod
    async def on_pre_output_coercion(
        directive_args, next_directive, value, field_definition, ctx, info
    ):
        print("-> on_pre_output_coercion")
        raise ValueError("on_pre_output_coercion error error")


@Scalar("CustomString", schema_name="test_input_directives")
class CustomScalar(ScalarString):
    pass


_SDL = """
directive @debug(message: String) on FIELD_DEFINITION | ARGUMENT_DEFINITION | INPUT_FIELD_DEFINITION | ENUM | ENUM_VALUE
directive @error on FIELD_DEFINITION | ARGUMENT_DEFINITION | INPUT_FIELD_DEFINITION | ENUM | ENUM_VALUE

scalar CustomString @debug(message: "CustomString")

enum ChannelOrderField @debug(message: "ChannelOrderField") {
  NAME @debug(message: "ChannelOrderField.NAME")
  CREATION_DATE @debug(message: "ChannelOrderField.CREATION_DATE")
}

enum OrderDirection @debug(message: "OrderDirection") {
  ASC @debug(message: "OrderDirection.ASC")
  DESC @debug(message: "OrderDirection.DESC")
}

input ChannelOrder @debug(message: "ChannelOrder") {
  field: ChannelOrderField! @debug(message: "ChannelOrder.field")
  direction: OrderDirection! @debug(message: "ChannelOrder.direction")
  useless: CustomString @debug(message: "ChannelOrder.useless")
}

enum Field @debug(message: "Field") {
  FIELD_1 @debug(message: "Field.FIELD_1")
  FIELD_2 @debug(message: "Field.FIELD_2")
}

input Filters @debug(message: "Filters") {
  groups: [String!] @debug(message: "Filters.groups") @error
  fields: [Field!] @debug(message: "Filters.fields") @error
}

input Complex @debug(message: "Complex") {
  filters: Filters! @debug(message: "Complex.filters")
}

type Channel {
  id: Int!
  name: String!
}

type Query {
  channelz(
    orderField: ChannelOrderField!
    orderDirection: OrderDirection!
    useless: CustomString
  ): [Channel]

  channels(
    order: ChannelOrder! @debug(message: "channels.order")
  ): [Channel]
  
  users(input: Complex!): Channel
}
"""

_TTFTT_ENGINE = Engine(_SDL, schema_name="test_input_directives")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query,variables,expected",
    [
        # (
        #     """
        #     query Channelz {
        #       channelz(
        #         orderField: NAME
        #         orderDirection: DESC
        #         useless: "..."
        #       ) {
        #         id
        #         name
        #       }
        #     }
        #     """,
        #     None,
        #     {"data": {"channelz": []}},
        # ),
        (
            """
            query Channelz(
              $orderField: ChannelOrderField!
              $orderDirection: OrderDirection!
              $useless: CustomString
            ) {
              channelz(
                orderField: $orderField
                orderDirection: $orderDirection
                useless: $useless
              ) {
                id
                name
              }
            }
            """,
            {"orderField": "NAME", "orderDirection": "DESC", "useless": "..."},
            {"data": {"channelz": []}},
        ),
        # (
        #     """
        #     query Channels {
        #       channels(order: {
        #         field: NAME
        #         direction: DESC
        #         useless: "..."
        #       }) {
        #         id
        #         name
        #       }
        #     }
        #     """,
        #     None,
        #     {"data": {"channels": []}},
        # ),
        (
            """
            query Channels($order: ChannelOrder!) {
              channels(order: $order) {
                id
                name
              }
            }
            """,
            {
                "order": {
                    "field": "NAME",
                    "direction": "DESC",
                    "useless": "...",
                }
            },
            {"data": {"channels": []}},
        ),
        # (
        #     """
        #     query Users {
        #       users(input: {
        #         filters: {
        #           groups: ["Group 1", null, "Group 2", null]
        #           fields: [FIELD_1, null, FIELD_2, null, UNKNOWN_FIELD]
        #         }
        #       }) {
        #         id
        #         name
        #       }
        #     }
        #     """,
        #     None,
        #     {
        #         "data": {"users": None},
        #         "errors": [
        #             {
        #                 "locations": [{"column": 15, "line": 3}],
        #                 "message": "Argument < input > has invalid value < {filters: {groups: [Group 1, null, Group 2, null], fields: [FIELD_1, null, FIELD_2, null, UNKNOWN_FIELD]}} >.",
        #                 "path": ["users"],
        #             }
        #         ],
        #     },
        # ),
        (
            """
            query Users($input: Complex!) {
              users(input: $input) {
                id
                name
              }
            }
            """,
            {
                "input": {
                    "filters": {
                        "groups": ["Group 1", None, "Group 2", None],
                        "fields": [
                            "FIELD_1",
                            None,
                            "FIELD_2",
                            None,
                            "UNKNOWN_FIELD",
                        ],
                    }
                }
            },
            {
                "data": None,
                "errors": [
                    {
                        "locations": [{"column": 25, "line": 2}],
                        "message": "Variable < $input > got invalid value < {'filters': {'groups': ['Group 1', None, 'Group 2', None], 'fields': ['FIELD_1', None, 'FIELD_2', None, 'UNKNOWN_FIELD']}} >; Expected non-nullable type < String! > not to be null at value.filters.groups[1].",
                        "path": None,
                    },
                    {
                        "locations": [{"column": 25, "line": 2}],
                        "message": "Variable < $input > got invalid value < {'filters': {'groups': ['Group 1', None, 'Group 2', None], 'fields': ['FIELD_1', None, 'FIELD_2', None, 'UNKNOWN_FIELD']}} >; Expected non-nullable type < String! > not to be null at value.filters.groups[3].",
                        "path": None,
                    },
                    {
                        "locations": [{"column": 25, "line": 2}],
                        "message": "Variable < $input > got invalid value < {'filters': {'groups': ['Group 1', None, 'Group 2', None], 'fields': ['FIELD_1', None, 'FIELD_2', None, 'UNKNOWN_FIELD']}} >; Expected non-nullable type < Field! > not to be null at value.filters.fields[1].",
                        "path": None,
                    },
                    {
                        "locations": [{"column": 25, "line": 2}],
                        "message": "Variable < $input > got invalid value < {'filters': {'groups': ['Group 1', None, 'Group 2', None], 'fields': ['FIELD_1', None, 'FIELD_2', None, 'UNKNOWN_FIELD']}} >; Expected non-nullable type < Field! > not to be null at value.filters.fields[3].",
                        "path": None,
                    },
                    {
                        "locations": [{"column": 25, "line": 2}],
                        "message": "Variable < $input > got invalid value < {'filters': {'groups': ['Group 1', None, 'Group 2', None], 'fields': ['FIELD_1', None, 'FIELD_2', None, 'UNKNOWN_FIELD']}} >; Expected type < Field > at value.filters.fields[4].",
                        "path": None,
                    },
                ],
            },
        ),
        (
            """
            query Users($input: Complex!) {
              users(input: $input) {
                id
                name
              }
            }
            """,
            {
                "input": {
                    "filters": {
                        "groups": ["Group 1", "Group 2"],
                        "fields": ["FIELD_1", "FIELD_2"],
                    }
                }
            },
            {
                "data": None,
                "errors": [
                    {
                        "locations": [{"column": 25, "line": 2}],
                        "message": "Variable < $input > got invalid value < {'filters': {'groups': ['Group 1', 'Group 2'], 'fields': ['FIELD_1', 'FIELD_2']}} >; on_post_input_coercion error at value.filters.groups.",
                        "path": None,
                    },
                    {
                        "locations": [{"column": 25, "line": 2}],
                        "message": "Variable < $input > got invalid value < {'filters': {'groups': ['Group 1', 'Group 2'], 'fields': ['FIELD_1', 'FIELD_2']}} >; on_post_input_coercion error at value.filters.fields.",
                        "path": None,
                    },
                ],
            },
        ),
    ],
)
async def test_input_directives_object(query, variables, expected):
    assert await _TTFTT_ENGINE.execute(query, variables=variables) == expected
