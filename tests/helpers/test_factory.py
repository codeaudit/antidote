import pytest

from antidote import DependencyContainer, factory
from antidote.providers import FactoryProvider, TagProvider


@pytest.fixture()
def container():
    c = DependencyContainer()
    c.register_provider(FactoryProvider())
    c.register_provider(TagProvider(container=c))

    return c


class Service:
    pass


class AnotherService:
    pass


class YetAnotherService:
    pass


class SuperService:
    pass


def test_function(container):
    @factory(builds=(Service,), container=container)
    def build():
        return Service()

    assert isinstance(container[Service], Service)
    # singleton by default
    assert container[Service] is container[Service]


def test_class(container):
    @factory(container=container, builds=(Service,))
    class ServiceFactory:
        def __call__(self):
            return Service()

    assert isinstance(container[Service], Service)
    # singleton by default
    assert container[Service] is container[Service]


def test_function_return_type_hint(container):
    @factory(container=container)
    def build() -> Service:
        return Service()

    assert isinstance(container[Service], Service)
    # singleton by default
    assert container[Service] is container[Service]


def test_class_return_type_hint(container):
    @factory(container=container)
    class ServiceFactory:
        def __call__(self) -> AnotherService:
            return AnotherService()

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]


def test_missing_dependency(container):
    with pytest.raises(ValueError):  # No dependency
        @factory(container=container)
        def faulty_service_provider():
            return Service()

    with pytest.raises(ValueError):
        @factory(container=container)
        class FaultyServiceFactory:
            def __call__(self):
                return Service()


def test_missing_call(container):
    with pytest.raises(ValueError):
        @factory(builds=(Service,), container=container)
        class FaultyServiceFactory2:
            pass


def test_invalid_register():
    with pytest.raises(ValueError):
        factory(1)

    with pytest.raises(ValueError):
        @factory
        class Test:
            pass
