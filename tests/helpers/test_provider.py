import pytest

from antidote import DependencyNotProvidableError, Instance
from antidote.helpers import new_container, provider
from antidote.providers import FactoryProvider, GetterProvider, Provider
from antidote.providers.tags import TagProvider


@pytest.fixture()
def container():
    return new_container()


def test_simple(container):
    container['service'] = object()

    @provider(container=container)
    class DummyProvider(Provider):
        def __antidote_provide__(self, dependency):
            if dependency.id == 'test':
                return Instance(dependency.id)
            else:
                raise DependencyNotProvidableError(dependency)

    assert isinstance(container.providers[DummyProvider], DummyProvider)
    assert 'test' == container['test']


def test_invalid_provider(container):
    with pytest.raises(TypeError):
        provider(object())

    with pytest.raises(ValueError):
        @provider
        class Dummy:
            pass

    with pytest.raises(TypeError):
        @provider
        class MissingAntidoteProvideMethod(Provider):
            pass

    with pytest.raises(TypeError):
        @provider(auto_wire=False, container=container)
        class MissingDependencyProvider(Provider):
            def __init__(self, service):
                self.service = service

            def __antidote_provide__(self, dependency):
                return Instance(dependency.id)


def test_providers(container):
    assert 3 == len(container.providers)
    assert FactoryProvider in container.providers
    assert GetterProvider in container.providers
    assert TagProvider in container.providers

    @provider(container=container)
    class DummyProvider(Provider):
        def __antidote_provide__(self, dependency):
            return Instance(1)

    assert DummyProvider in container.providers
