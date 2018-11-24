import functools

import pytest

from antidote import (DependencyContainer, DependencyInstantiationError,
                      FactoryProvider, Tag, TagProvider, Tagged)
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


def test_type_hints(container):
    register_ = functools.partial(register, container=container)

    @register_
    class Service:
        pass

    @register_
    class AnotherService:
        def __init__(self, service: Service):
            self.service = service

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]
    assert container[Service] is container[AnotherService].service

    @register_(use_type_hints=False)
    class BrokenService:
        def __init__(self, service: Service):
            self.service = service

    with pytest.raises(TypeError):
        BrokenService()

    with pytest.raises(DependencyInstantiationError):
        container[BrokenService]


def test_arg_map(container):
    register_ = functools.partial(register, container=container)

    @register_
    class Service:
        pass

    @register_(arg_map=dict(service=Service))
    class AnotherService:
        def __init__(self, service):
            self.service = service

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]
    assert container[Service] is container[AnotherService].service

    @register_(arg_map=(None, Service,))
    class AnotherService:
        def __init__(self, s):
            self.service = s

    assert isinstance(container[AnotherService], AnotherService)
    # singleton by default
    assert container[AnotherService] is container[AnotherService]
    assert container[Service] is container[AnotherService].service


def test_use_names(container):
    container['service'] = object()

    @register(use_names=True, container=container)
    class YetAnotherService:
        def __init__(self, service):
            self.service = service

    assert isinstance(container[YetAnotherService], YetAnotherService)
    # singleton by default
    assert container[YetAnotherService] is container[YetAnotherService]
    assert container['service'] is container[YetAnotherService].service


def test_non_singleton(container):
    @register(singleton=False, container=container)
    class SingleUsageService:
        pass

    assert isinstance(container[SingleUsageService], SingleUsageService)
    assert container[SingleUsageService] is not container[SingleUsageService]


def test_no_auto_wire(container):
    @register(auto_wire=False, container=container)
    class BrokenService:
        def __init__(self, service):
            self.service = service

    with pytest.raises(TypeError):
        BrokenService()

    with pytest.raises(DependencyInstantiationError):
        container[BrokenService]


def test_complex_auto_wire(container):
    register_ = functools.partial(register, container=container)

    container['x'] = object()

    @register_
    class Service:
        pass

    @register_(auto_wire=('__init__', 'method'),
               arg_map=dict(service=Service, x='x'))
    class ComplexWiringService:
        def __init__(self, service):
            self.service = service

        def method(self, x):
            return x

    assert isinstance(container[ComplexWiringService], ComplexWiringService)
    assert container[Service] is container[ComplexWiringService].service
    assert container['x'] is container[ComplexWiringService].method()


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
