import pytest

from antidote.exceptions import DuplicateDependencyError
from antidote.providers.factory import Build, FactoryProvider


class Service:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class AnotherService:
    def __init__(self, *args):
        pass


@pytest.fixture()
def provider():
    return FactoryProvider()


def test_register(provider: FactoryProvider):
    provider.register(Service, Service)

    dependency = provider.provide(Service)
    assert isinstance(dependency.instance, Service)
    assert repr(Service) in repr(provider)


def test_register_factory_id(provider: FactoryProvider):
    provider.register(Service, lambda: Service())

    dependency = provider.provide(Service)
    assert isinstance(dependency.instance, Service)


def test_singleton(provider: FactoryProvider):
    provider.register(Service, Service, singleton=True)
    provider.register(AnotherService, AnotherService, singleton=False)

    provide = provider.provide
    assert provide(Service).singleton is True
    assert provide(AnotherService).singleton is False


def test_takes_dependency(provider: FactoryProvider):
    provider.register(Service, lambda cls: cls(), takes_dependency=True)

    assert isinstance(
        provider.provide(Service).instance,
        Service
    )

    assert provider.provide(AnotherService) is None


def test_build_dependency(provider: FactoryProvider):
    provider.register(Service, Service)

    s = provider.provide(Build(Service, 1, val=object)).instance
    assert isinstance(s, Service)
    assert (1,) == s.args
    assert dict(val=object) == s.kwargs


def test_invalid_register_not_callable(provider: FactoryProvider):
    with pytest.raises(ValueError):
        provider.register(1, 1)


def test_invalid_register_id_null(provider: FactoryProvider):
    with pytest.raises(ValueError):
        provider.register(None, Service)


def test_duplicate_error(provider: FactoryProvider):
    provider.register(Service, Service)

    with pytest.raises(DuplicateDependencyError):
        provider.register(Service, Service)

    with pytest.raises(DuplicateDependencyError):
        provider.register(Service, lambda: Service())
