import pytest


async def _query_humans_resolver(_parent_result, args, *_, **__):
    return [{"name": "Hooman %s" % human_id} for human_id in args["ids"]]


async def _query_dog_resolver(*_, **__):
    return {
        "name": "Doggo",
        "nickname": None,
        "barkVolume": 1,
        "owner": {"name": "Hooman"},
    }


async def _dog_does_know_command_resolver(_parent_result, args, *_, **__):
    return args["dogCommand"] in ["SIT", "DOWN"]


async def _dog_is_housetrained_resolver(_parent_result, args, *_, **__):
    return not args["atOtherHomes"]


async def _query_cat_or_dog_resolver(*_, **__):
    return {
        "__typename": "Cat",
        "name": "Cat",
        "nickname": None,
        "meowVolume": 2,
    }


@pytest.mark.asyncio
@pytest.mark.ttftt_engine(
    resolvers={
        "Query.humans": _query_humans_resolver,
        "Query.dog": _query_dog_resolver,
        "Dog.doesKnowCommand": _dog_does_know_command_resolver,
        "Dog.isHousetrained": _dog_is_housetrained_resolver,
    }
)
@pytest.mark.parametrize(
    "query,operation_name,variables,expected",
    [
        (
            """
            fragment DogFields on Dog {
              name
              nickname
            }
            
            query {
              ... on Query {
                dog {
                  ...DogFields
                }
                dog {
                  barkVolume
                }
              }
            }
            """,
            None,
            None,
            {
                "data": {
                    "dog": {"name": "Doggo", "nickname": None, "barkVolume": 1}
                }
            },
        ),
        (
            """
            fragment DogFields on Dog {
              name
              nickname
              barkVolume
            }
            
            fragment HumanFields on Human {
              name
            }
            
            query Dog {
              dog {
                ...DogFields
                owner {
                  ...HumanFields
                }
              }
            }
            
            query Human {
              humans(ids: [1]) {
                ... on Human {
                  name
                }
              }
            }
            """,
            "Dog",
            None,
            {
                "data": {
                    "dog": {
                        "name": "Doggo",
                        "nickname": None,
                        "barkVolume": 1,
                        "owner": {"name": "Hooman"},
                    }
                }
            },
        ),
        (
            """
            fragment DogFields on Dog {
              name
              nickname
              barkVolume
            }
            
            query Dog($dogCommand: DogCommand! = HEEL) {
              dogo: dog {
                ...DogFields
                doesKnowCommand(dogCommand: $dogCommand)
              }
            }
            """,
            None,
            {"dogCommand": "SIT"},
            {
                "data": {
                    "dogo": {
                        "name": "Doggo",
                        "nickname": None,
                        "barkVolume": 1,
                        "doesKnowCommand": True,
                    }
                }
            },
        ),
        (
            """
            fragment DogFields on Dog {
              name
              nickname
              barkVolume
            }
            
            fragment HumanFields on Human {
              name
            }
            
            query Dog($dogCommand: DogCommand! = HEEL) {
              dogo: dog {
                ...DogFields
                doesKnowCommand(dogCommand: $dogCommand)
              }
              humans(ids: [1]) {
                ... on Human {
                  ...HumanFields
                }
              }
            }
            """,
            None,
            {"dogCommand": "SIT"},
            {
                "data": {
                    "dogo": {
                        "name": "Doggo",
                        "nickname": None,
                        "barkVolume": 1,
                        "doesKnowCommand": True,
                    },
                    "humans": [{"name": "Hooman 1"}],
                }
            },
        ),
        (
            """
            fragment DogFields on Dog {
              name
              nickname
              barkVolume
            }
            
            fragment HumanFields on Human {
              name
            }
            
            query {
              catOrDog {
                ...HumanFields
                ...DogFields
                ... on Cat {
                  name
                  nickname
                  meowVolume
                }
              }
            }
            """,
            None,
            {"dogCommand": "SIT"},
            {
                "data": {
                    "catOrDog": {
                        "name": "Cat",
                        "nickname": None,
                        "meowVolume": 2,
                    }
                }
            },
        ),
    ],
)
async def test_refactoring(engine, query, operation_name, variables, expected):
    assert (
        await engine.execute(
            query, operation_name=operation_name, variable_values=variables
        )
        == expected
    )
