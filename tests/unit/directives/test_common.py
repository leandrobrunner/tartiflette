import pytest


def test_common_directive_creation():
    from tartiflette.directive.common import CommonDirective

    c = CommonDirective()

    assert c is not None
    assert hasattr(c, "on_build")
    assert hasattr(c, "on_introspection")
    assert hasattr(c, "on_field_execution")
    assert hasattr(c, "on_argument_execution")


@pytest.mark.asyncio
async def test_common_directives_on_field_execution_call():
    from tartiflette.directive.common import CommonDirective
    from unittest.mock import Mock

    a = Mock()

    async def lol(*args, **kwargs):
        a(*args, **kwargs)

    await CommonDirective.on_field_execution(
        {}, lol, "PARIS", "EST", "MAGIC", "!"
    )

    assert a.called_with("PARIS", "EST", "MAGIC", "!")


@pytest.mark.asyncio
async def test_common_directives_on_argument_execution_call():
    from tartiflette.directive.common import CommonDirective
    from unittest.mock import Mock

    a = Mock()

    async def lol(*args, **kwargs):
        a(*args, **kwargs)

    await CommonDirective.on_argument_execution(
        {}, lol, "PARIS", "EST", "MAGIC", "!"
    )

    assert a.called_with("PARIS", "EST", "MAGIC", "!")


@pytest.mark.asyncio
async def test_common_directives_on_introspection_call():
    from tartiflette.directive.common import CommonDirective
    from unittest.mock import Mock

    b = Mock()

    async def c2(*args, **kwargs):
        b(*args, **kwargs)

    await CommonDirective.on_introspection({}, c2, "IE", None, None)

    assert b.called_with("IE")


def test_common_directives_on_build_call():
    from tartiflette.directive.common import CommonDirective

    assert not CommonDirective.on_build(None)
