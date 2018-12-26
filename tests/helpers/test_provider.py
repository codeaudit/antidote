import pytest

from antidote import DependencyInstance, DependencyProvider, new_container, provider
from antidote.exceptions import DependencyNotProvidableError
from antidote.providers import FactoryProvider, ResourceProvider, TagProvider


@pytest.fixture()
def container():
    return new_container()


def test_simple(container):
    container['service'] = object()

    @provider(container=container)
    class DummyProvider(DependencyProvider):
        def provide(self, dependency):
            if dependency == 'test':
                return DependencyInstance(dependency)
            else:
                raise DependencyNotProvidableError(dependency)

    assert isinstance(container.providers[DummyProvider], DummyProvider)
    assert 'test' == container['test']


def test_invalid_provider(container):
    with pytest.raises(TypeError):
        provider(object(), container=container)

    with pytest.raises(ValueError):
        @provider(container=container)
        class Dummy:
            pass

    with pytest.raises(TypeError):
        @provider(auto_wire=False, container=container)
        class MissingDependencyProvider(DependencyProvider):
            def __init__(self, service):
                self.service = service

            def provide(self, dependency):
                return DependencyInstance(dependency)


def test_providers(container):
    assert 3 == len(container.providers)
    assert FactoryProvider in container.providers
    assert ResourceProvider in container.providers
    assert TagProvider in container.providers

    @provider(container=container)
    class DummyProvider(DependencyProvider):
        def provide(self, dependency):
            return DependencyInstance(1)

    assert DummyProvider in container.providers
