from typing import List, Optional, Union

from tartiflette.json_parsing.nodes import (
    ArgumentNode,
    BooleanValueNode,
    DirectiveNode,
    DocumentNode,
    EnumValueNode,
    FieldNode,
    FloatValueNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    IntValueNode,
    ListTypeNode,
    ListValueNode,
    NamedTypeNode,
    NameNode,
    NonNullTypeNode,
    NullValueNode,
    ObjectFieldNode,
    ObjectValueNode,
    OperationDefinitionNode,
    SelectionSetNode,
    StringValueNode,
    VariableDefinitionNode,
    VariableNode,
)
from tartiflette.types.location import Location


def parse_location(location) -> "Location":
    """
    TODO:
    :param location: TODO:
    :return: TODO:
    """
    return Location(
        line=location["start"]["line"],
        column=location["start"]["column"],
        line_end=location["end"]["line"],
        column_end=location["end"]["column"],
    )


def parse_name(name) -> "NameNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#sec-Names
    > Name :: /[_A-Za-z][_0-9A-Za-z]*/

    :param name: TODO:
    :return: TODO:
    """
    return NameNode(value=name["value"], location=parse_location(name["loc"]))


def parse_named_type(named_type) -> "NamedTypeNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#NamedType
    > NamedType : Name

    :param named_type: TODO:
    :return: TODO:
    """
    return NamedTypeNode(
        name=parse_name(named_type["name"]),
        location=parse_location(named_type["loc"]),
    )


def parse_variable(variable) -> "VariableNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#Variable
    > Variable : $ Name

    :param variable: TODO:
    :return: TODO:
    """
    return VariableNode(
        name=parse_name(variable["name"]),
        location=parse_location(variable["loc"]),
    )


def parse_boolean_value(boolean_value) -> "BooleanValueNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#BooleanValue
    > BooleanValue : one of
    >   true false

    :param boolean_value: TODO:
    :return: TODO:
    """
    return BooleanValueNode(
        value=boolean_value["value"],
        location=parse_location(boolean_value["loc"]),
    )


def parse_enum_value(enum_value) -> "EnumValueNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#EnumValue
    > EnumValue : Name

    :param enum_value: TODO:
    :return: TODO:
    """
    return EnumValueNode(
        value=enum_value["value"], location=parse_location(enum_value["loc"])
    )


def parse_float_value(float_value) -> "FloatValueNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#FloatValue
    > FloatValue ::
    >   - IntegerPart FractionalPart
    >   - IntegerPart ExponentPart
    >   - IntegerPart FractionalPart ExponentPart

    :param float_value: TODO:
    :return: TODO:
    """
    return FloatValueNode(
        value=float_value["value"], location=parse_location(float_value["loc"])
    )


def parse_int_value(int_value) -> "IntValueNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#IntValue
    > IntValue :: IntegerPart

    :param int_value: TODO:
    :return: TODO:
    """
    return IntValueNode(
        value=int_value["value"], location=parse_location(int_value["loc"])
    )


def parse_values(
    values
) -> List[
    Union[
        "BooleanValue",
        "EnumValue",
        "FloatValue",
        "IntValue",
        "ListValue",
        "NullValue",
        "ObjectValue",
        "StringValue",
        "Variable",
    ]
]:
    """
    TODO:
    :param values: TODO:
    :return: TODO:
    """
    if values:
        return [parse_value(value) for value in values]
    return []


def parse_list_value(list_value) -> "ListValueNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#ListValue
    > ListValue[Const] :
    >   - [ ]
    >   - [ Value[?Const]+ ]

    :param list_value: TODO:
    :return: TODO:
    """
    return ListValueNode(
        values=parse_values(list_value["values"]),
        location=parse_location(list_value["loc"]),
    )


def parse_null_value(null_value) -> "NullValueNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#NullValue
    > NullValue : null

    :param null_value: TODO:
    :return: TODO:
    """
    return NullValueNode(
        value=None, location=parse_location(null_value["loc"])
    )


def parse_object_field(object_field) -> "ObjectFieldNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#ObjectField
    > ObjectField[Const] : Name : Value[?Const]

    :param object_field: TODO:
    :return: TODO:
    """
    return ObjectFieldNode(
        name=parse_name(object_field["name"]),
        value=parse_value(object_field["value"]),
        location=parse_location(object_field["loc"]),
    )


def parse_object_fields(object_fields) -> List["ObjectFieldNode"]:
    """
    TODO:
    :param object_fields: TODO:
    :return: TODO:
    """
    if object_fields:
        return [
            parse_object_field(object_field) for object_field in object_fields
        ]
    return []


def parse_object_value(object_value) -> "ObjectValueNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#ObjectValue
    > ObjectValue[Const] :
    >   - { }
    >   - { ObjectField[?Const]+ }

    :param object_value: TODO:
    :return: TODO:
    """
    return ObjectValueNode(
        fields=parse_object_fields(object_value["fields"]),
        location=parse_location(object_value["loc"]),
    )


def parse_string_value(string_value) -> "StringValueNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#StringValue
    > StringValue ::
    >   - "StringCharacter+"

    :param string_value: TODO:
    :return: TODO:
    """
    return StringValueNode(
        value=string_value["value"],
        location=parse_location(string_value["loc"]),
    )


_VALUE_PARSER_MAPPING = {
    "BooleanValue": parse_boolean_value,
    "EnumValue": parse_enum_value,
    "FloatValue": parse_float_value,
    "IntValue": parse_int_value,
    "ListValue": parse_list_value,
    "NullValue": parse_null_value,
    "ObjectValue": parse_object_value,
    "StringValue": parse_string_value,
    "Variable": parse_variable,
}


def parse_value(
    value
) -> Optional[
    Union[
        "BooleanValue",
        "EnumValue",
        "FloatValue",
        "IntValue",
        "ListValue",
        "NullValue",
        "ObjectValue",
        "StringValue",
        "Variable",
    ]
]:
    """
    TODO:
    :param value: TODO:
    :return: TODO:
    """
    if value:
        return _VALUE_PARSER_MAPPING[value["kind"]](value)
    return None


def parse_argument(argument) -> "ArgumentNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#Argument
    > Argument[Const] : Name : Value[?Const]

    :param argument: TODO:
    :return: TODO:
    """
    return ArgumentNode(
        name=parse_name(argument["name"]),
        value=parse_value(argument["value"]),
        location=parse_location(argument["loc"]),
    )


def parse_arguments(arguments) -> List["ArgumentNode"]:
    """
    TODO:
    :param arguments: TODO:
    :return: TODO:
    """
    if arguments:
        return [parse_argument(argument) for argument in arguments]
    return []


def parse_directive(directive) -> "DirectiveNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#Directive
    > Directive[Const] : @ Name Arguments[?Const]?

    :param directive: TODO:
    :return: TODO:
    """
    return DirectiveNode(
        name=parse_name(directive["name"]),
        arguments=parse_arguments(directive["arguments"]),
        location=parse_location(directive["loc"]),
    )


def parse_directives(directives) -> List["DirectiveNode"]:
    """
    TODO:
    :param directives: TODO:
    :return: TODO:
    """
    if directives:
        return [parse_directive(directive) for directive in directives]
    return []


def parse_field(field) -> "FieldNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#Field
    > Field : Alias? Name Arguments? Directives? SelectionSet?

    :param field: TODO:
    :return: TODO:
    """
    return FieldNode(
        alias=parse_name(field["alias"]) if field["alias"] else None,
        name=parse_name(field["name"]),
        arguments=parse_arguments(field["arguments"]),
        directives=parse_directives(field["directives"]),
        selection_set=parse_selection_set(field["selectionSet"]),
        location=parse_location(field["loc"]),
    )


def parse_fragment_spread(fragment_spread) -> "FragmentSpreadNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#FragmentSpread
    > FragmentSpread : ... FragmentName Directives?

    :param fragment_spread: TODO:
    :return: TODO:
    """
    return FragmentSpreadNode(
        name=parse_name(fragment_spread["name"]),
        directives=parse_directives(fragment_spread["directives"]),
        location=parse_location(fragment_spread["loc"]),
    )


def parse_inline_fragment(inline_fragment) -> "InlineFragmentNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#InlineFragment
    > InlineFragment : ... TypeCondition? Directives? SelectionSet

    :param inline_fragment: TODO:
    :return: TODO:
    """
    return InlineFragmentNode(
        directives=parse_directives(inline_fragment["directives"]),
        type_condition=parse_named_type(inline_fragment["typeCondition"])
        if inline_fragment["typeCondition"]
        else None,
        selection_set=parse_selection_set(inline_fragment["selectionSet"]),
        location=parse_location(inline_fragment["loc"]),
    )


_SELECTION_PARSER_MAPPING = {
    "Field": parse_field,
    "FragmentSpread": parse_fragment_spread,
    "InlineFragment": parse_inline_fragment,
}


def parse_selection(
    selection
) -> Union["FieldNode", "FragmentSpreadNode", "InlineFragmentNode"]:
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#Selection
    > Selection :
    >   - Field
    >   - FragmentSpread
    >   - InlineFragment

    :param selection: TODO:
    :return: TODO:
    """
    return _SELECTION_PARSER_MAPPING[selection["kind"]](selection)


def parse_selections(
    selections
) -> List[Union["FieldNode", "FragmentSpreadNode", "InlineFragmentNode"]]:
    """
    TODO:
    :param selections: TODO:
    :return: TODO:
    """
    if selections:
        return [parse_selection(selection) for selection in selections]
    return []


def parse_selection_set(selection_set) -> Optional["SelectionSetNode"]:
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#SelectionSet
    > SelectionSet : { Selection+ }

    :param selection_set: TODO:
    :return: TODO:
    """
    if selection_set:
        return SelectionSetNode(
            selections=parse_selections(selection_set["selections"]),
            location=parse_location(selection_set["loc"]),
        )
    return None


def parse_fragment_definition(fragment_definition) -> "FragmentDefinitionNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#FragmentDefinition
    > FragmentDefinition :
    > fragment FragmentName on TypeCondition Directives? SelectionSet

    :param fragment_definition: TODO:
    :return: TODO:
    """
    return FragmentDefinitionNode(
        name=parse_name(fragment_definition["name"]),
        type_condition=parse_named_type(fragment_definition["typeCondition"]),
        directives=parse_directives(fragment_definition["directives"]),
        selection_set=parse_selection_set(fragment_definition["selectionSet"]),
        location=parse_location(fragment_definition["loc"]),
    )


def parse_type_reference(
    type_reference
) -> Union["ListTypeNode", "NonNullTypeNode", "NamedTypeNode"]:
    """
    TODO:
    :param type_reference: TODO:
    :return: TODO:
    """
    if type_reference["kind"] == "ListType":
        return ListTypeNode(
            type_reference=parse_type_reference(type_reference["type"]),
            location=parse_location(type_reference["loc"]),
        )
    if type_reference["kind"] == "NonNullType":
        return NonNullTypeNode(
            type_reference=parse_type_reference(type_reference["type"]),
            location=parse_location(type_reference["loc"]),
        )
    return parse_named_type(type_reference)


def parse_variable_definition(variable_definition) -> "VariableDefinitionNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#VariableDefinition
    > VariableDefinition : Variable : Type DefaultValue? Directives[Const]?

    :param variable_definition: TODO:
    :return: TODO:
    """
    return VariableDefinitionNode(
        variable=parse_variable(variable_definition["variable"]),
        type_reference=parse_type_reference(variable_definition["type"]),
        default_value=parse_value(variable_definition["defaultValue"]),
        location=parse_location(variable_definition["loc"]),
    )


def parse_variable_definitions(
    variable_definitions
) -> List["VariableDefinitionNode"]:
    """
    TODO:
    :param variable_definitions: TODO:
    :return: TODO:
    """
    if variable_definitions:
        return [
            parse_variable_definition(variable_definition)
            for variable_definition in variable_definitions
        ]
    return []


def parse_operation_definition(
    operation_definition
) -> "OperationDefinitionNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#OperationDefinition
    > OperationDefinition :
    >    - OperationType Name? VariableDefinitions? Directives? SelectionSet
    >    - SelectionSet

    :param operation_definition: TODO:
    :return: TODO:
    """
    return OperationDefinitionNode(
        operation=operation_definition["operation"],
        name=parse_name(operation_definition["name"])
        if operation_definition["name"]
        else None,
        variable_definitions=parse_variable_definitions(
            operation_definition["variableDefinitions"]
        ),
        directives=parse_directives(operation_definition["directives"]),
        selection_set=parse_selection_set(
            operation_definition["selectionSet"]
        ),
        location=parse_location(operation_definition["loc"]),
    )


_DEFINITION_PARSER_MAPPING = {
    "FragmentDefinition": parse_fragment_definition,
    "OperationDefinition": parse_operation_definition,
}


def parse_definition(
    definition
) -> Union["FragmentDefinitionNode", "OperationDefinitionNode"]:
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#Definition
    > Definition :
    >   - ExecutableDefinition
    >   - TypeSystemDefinition
    >   - TypeSystemExtension

    :param definition: TODO:
    :return: TODO:
    """
    return _DEFINITION_PARSER_MAPPING[definition["kind"]](definition)


def parse_definitions(
    definitions
) -> List[Union["FragmentDefinitionNode", "OperationDefinitionNode"]]:
    """
    TODO:
    :param definitions: TODO:
    :return: TODO:
    """
    if definitions:
        return [parse_definition(definition) for definition in definitions]
    return []


def parse_document(document) -> "DocumentNode":
    """
    TODO:

    > GraphQL specification:
    > https://facebook.github.io/graphql/June2018/#sec-Language.Document
    > Document : Definition+

    :param document: TODO:
    :return: TODO:
    """
    return DocumentNode(
        definitions=parse_definitions(document["definitions"]),
        location=parse_location(document["loc"]),
    )
