import functools

import pytest

from antidote import (DependencyContainer, DependencyInstantiationError,
                      FactoryProvider, TagProvider)
from antidote.helpers import factory


@pytest.fixture()
def container():
    c = DependencyContainer()
    c.providers[FactoryProvider] = FactoryProvider()
    c.providers[TagProvider] = TagProvider(container=c)

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
    @factory(dependency_id=Service, container=container)
    def build():
        return Service()

    assert isinstance(container[Service], Service)
    # singleton by default
    assert container[Service] is container[Service]


def test_class(container):
    @factory(container=container, dependency_id=Service)
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


def test_function_type_hints(container):
    factory_ = functools.partial(factory, container=container)
    container[Service] = Service()

    @factory_
    def build(s: Service) -> AnotherService:
        a = AnotherService()
        a.service = s
        return a

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]
    assert container[Service] is container[AnotherService].service

    @factory_(use_type_hints=False)
    def build(s: Service) -> YetAnotherService:
        return YetAnotherService()

    with pytest.raises(TypeError):
        build()

    with pytest.raises(DependencyInstantiationError):
        container[YetAnotherService]


def test_class_type_hints(container):
    factory_ = functools.partial(factory, container=container)
    container[Service] = Service()

    @factory_
    class AnotherServiceFactory:
        def __call__(self, s: Service) -> AnotherService:
            a = AnotherService()
            a.service = s
            return a

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]
    assert container[Service] is container[AnotherService].service

    @factory_
    class AnotherServiceFactory:
        def __init__(self, s: Service):
            self.service = s

        def __call__(self, s: AnotherService) -> YetAnotherService:
            a = YetAnotherService()
            a.service = self.service
            a.another_service = s
            return a

    assert isinstance(container[YetAnotherService], YetAnotherService)
    # singleton by default
    assert container[YetAnotherService] is container[YetAnotherService]
    assert container[Service] is container[YetAnotherService].service
    assert container[AnotherService] is container[YetAnotherService].another_service

    with pytest.raises(TypeError):
        @factory_(use_type_hints=False)
        class AnotherServiceFactory:
            def __init__(self, s: Service):
                self.service = s

            def __call__(self, s: Service) -> SuperService:
                return SuperService()

    @factory_(use_type_hints=False)
    class AnotherServiceFactory:
        def __call__(self, s: Service) -> SuperService:
            return SuperService()

    with pytest.raises(TypeError):
        AnotherServiceFactory()()

    with pytest.raises(DependencyInstantiationError):
        container[SuperService]


def test_function_arg_map(container):
    factory_ = functools.partial(factory, container=container)
    container[Service] = Service()

    @factory_(arg_map=dict(service=Service))
    def another_service_provider(service) -> AnotherService:
        a = AnotherService()
        a.service = service
        return a

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]
    assert container[Service] is container[AnotherService].service

    @factory_(arg_map=(Service,))
    def another_service_provider(s) -> YetAnotherService:
        x = YetAnotherService()
        x.service = s
        return x

    assert isinstance(container[YetAnotherService], YetAnotherService)
    # singleton by default
    assert container[YetAnotherService] is container[YetAnotherService]
    assert container[Service] is container[YetAnotherService].service


def test_class_arg_map(container):
    factory_ = functools.partial(factory, container=container)
    container[Service] = Service()
    container[AnotherService] = AnotherService()

    @factory_(arg_map=dict(service=Service))
    class ServiceFactory:
        def __init__(self, service: Service):
            self.service = service

        def __call__(self, another_service: AnotherService) -> YetAnotherService:
            a = YetAnotherService()
            a.service = self.service
            a.another_service = another_service
            return a

    assert isinstance(container[YetAnotherService], YetAnotherService)
    # singleton by default
    assert container[YetAnotherService] is container[YetAnotherService]
    assert container[Service] is container[YetAnotherService].service
    assert container[AnotherService] is container[YetAnotherService].another_service

    @factory_(arg_map=(None, Service,))
    class ServiceFactory:
        def __call__(self, s) -> SuperService:
            a = SuperService()
            a.service = s
            return a

    assert isinstance(container[SuperService], SuperService)
    # singleton by default
    assert container[SuperService] is container[SuperService]
    assert container[Service] is container[SuperService].service


def test_function_use_names(container):
    factory_ = functools.partial(factory, container=container)
    container.update({'test': object(),
                      'service': object(),
                      Service: Service()})

    @factory_(use_names=True)
    def injected_by_name_provider(test) -> AnotherService:
        s = AnotherService()
        s.test = test
        return s

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]
    assert container['test'] is container[AnotherService].test

    @factory_(use_names=('test',))
    def injected_by_name_provider(test, service: Service) -> YetAnotherService:
        s = YetAnotherService()
        s.service = service
        s.test = test
        return s

    assert isinstance(container[YetAnotherService], YetAnotherService)
    # singleton by default
    assert container[YetAnotherService] is container[YetAnotherService]
    assert container['test'] is container[YetAnotherService].test
    assert container[Service] is container[YetAnotherService].service


def test_class_use_names(container):
    factory_ = functools.partial(factory, container=container)
    container.update({'test': object(),
                      'service': object(),
                      'hell_yeah': object(),
                      Service: Service()})

    @factory_(use_names=True)
    class ServiceFactory:
        def __init__(self, service):
            self.service = service

        def __call__(self, test) -> AnotherService:
            a = AnotherService()
            a.service = self.service
            a.test = test
            return a

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]
    assert container['test'] is container[AnotherService].test
    assert container['service'] is container[AnotherService].service

    @factory_(use_names=('hell_yeah',))
    class ServiceFactory:
        def __init__(self, service: Service, hell_yeah):
            self.service = service
            self.hell_yeah = hell_yeah

        def __call__(self, test: Service, hell_yeah) -> YetAnotherService:
            a = YetAnotherService()
            assert self.hell_yeah is hell_yeah
            a.hell_yeah = self.hell_yeah
            a.service = test
            return a

    assert isinstance(container[YetAnotherService], YetAnotherService)
    # singleton by default
    assert container[YetAnotherService] is container[YetAnotherService]
    assert container['hell_yeah'] is container[YetAnotherService].hell_yeah
    assert container[Service] is container[YetAnotherService].service


def test_function_non_singleton(container):
    @factory(singleton=False, container=container)
    def build() -> Service:
        return Service()

    assert isinstance(container[Service], Service)
    assert container[Service] is not container[Service]


def test_class_non_singleton(container):
    @factory(singleton=False, container=container)
    class ServiceFactory:
        def __call__(self) -> Service:
            return Service()

    assert isinstance(container[Service], Service)
    assert container[Service] is not container[Service]


def test_function_auto_wire(container):
    factory_ = functools.partial(factory, container=container)
    container.update({'service': object(),
                      Service: Service()})

    @factory_(auto_wire=False, use_names=True, use_type_hints=True)
    def faulty_service_provider(service: Service) -> AnotherService:
        return AnotherService()

    with pytest.raises(TypeError):
        faulty_service_provider()

    faulty_service_provider(container[Service])


def test_class_auto_wire(container):
    container.update({'service': object(),
                      'test': object(),
                      Service: Service()})

    @factory(auto_wire=('__init__', '__call__', 'method'),
             use_names=True, container=container)
    class ServiceFactory:
        def __init__(self, service: Service):
            self.service = service

        def __call__(self, service) -> AnotherService:
            a = AnotherService()
            a.service = service
            a.init_service = self.service
            a.method = self.method()
            return a

        def method(self, test):
            return test

    assert isinstance(container[AnotherService], AnotherService)
    assert container[AnotherService] is container[AnotherService]
    assert container['test'] is container[AnotherService].method
    assert container['service'] is container[AnotherService].service
    assert container[Service] is container[AnotherService].init_service


def test_class_no_auto_wire(container):
    factory_ = functools.partial(factory, container=container)
    container.update({'service': object(),
                      Service: Service()})

    with pytest.raises(TypeError):
        @factory_(auto_wire=False, use_names=True, use_type_hints=True)
        class FaultyServiceFactory:
            def __init__(self, service: Service):
                pass

            def __call__(self) -> AnotherService:
                return AnotherService()

    @factory_(auto_wire=False, use_names=True, use_type_hints=True)
    class FaultyServiceFactory2:
        def __call__(self, service: Service) -> YetAnotherService:
            return YetAnotherService()

    with pytest.raises(TypeError):
        FaultyServiceFactory2()()

    FaultyServiceFactory2()(container[Service])

    with pytest.raises(DependencyInstantiationError):
        container[YetAnotherService]


def test_missing_dependency_id(container):
    with pytest.raises(ValueError):  # No dependency ID
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
        @factory(dependency_id=Service, container=container)
        class FaultyServiceFactory2:
            pass


def test_invalid_register():
    with pytest.raises(ValueError):
        factory(1)

    with pytest.raises(ValueError):
        @factory
        class Test:
            pass
