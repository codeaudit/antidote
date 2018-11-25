import pytest

from antidote import (DependencyContainer, FactoryProvider, Tag, TagProvider, Tagged)
from antidote.helpers import register


@pytest.fixture()
def container():
    c = DependencyContainer()
    c.providers[FactoryProvider] = FactoryProvider()
    c.providers[TagProvider] = TagProvider(container=c)

    return c


def test_simple(container):
    @register(container=container)
    class Service:
        pass

    assert isinstance(container[Service], Service)
    # singleton by default
    assert container[Service] is container[Service]


def test_non_singleton(container):
    @register(singleton=False, container=container)
    class SingleUsageService:
        pass

    assert isinstance(container[SingleUsageService], SingleUsageService)
    assert container[SingleUsageService] is not container[SingleUsageService]


def test_tags(container):
    @register(container=container, tags=[Tag('dummy')])
    class Service:
        pass

    tagged = list(container[Tagged('dummy')])
    assert 1 == len(tagged)
    assert isinstance(tagged[0], Service)
    assert container[Service] is tagged[0]


def test_invalid_register(container):
    with pytest.raises(ValueError):
        register(object())

    def f():
        pass

    with pytest.raises(ValueError):
        register(f)
