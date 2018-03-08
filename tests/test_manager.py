import pytest

from antidote.manager import DependencyManager
from antidote import DependencyInstantiationError
from antidote.container import (
    Dependency, DependencyNotProvidableError, DependencyNotFoundError
)


def test_inject_bind():
    manager = DependencyManager()
    container = manager.container

    class Service(object):
        pass

    manager.register(Service)

    @manager.inject(bind=True)
    def f(x):
        return x

    with pytest.raises(TypeError):
        f()

    @manager.inject(mapping=dict(x=Service), bind=True)
    def g(x):
        return x

    assert container[Service] is g()

    # arguments are bound, so one should not be able to pass injected
    # argument.
    with pytest.raises(TypeError):
        g(1)

    container['service'] = container[Service]
    container['service_bis'] = container[Service]

    @manager.inject(use_names=True, bind=True)
    def h(service, service_bis=None):
        return service, service_bis

    result = h()
    assert container[Service] is result[0]
    assert container[Service] is result[1]

    @manager.inject(use_names=('service',), bind=True)
    def h(service, service_bis=None):
        return service, service_bis

    result = h()
    assert container[Service] is result[0]
    assert None is result[1]


def test_inject_with_mapping():
    manager = DependencyManager()
    container = manager.container

    class Service(object):
        pass

    manager.register(Service)

    class AnotherService(object):
        pass

    manager.register(AnotherService)

    @manager.inject
    def f(x):
        return x

    with pytest.raises(TypeError):
        f()

    @manager.inject(mapping=dict(x=Service))
    def g(x):
        return x

    assert container[Service] is g()

    @manager.inject(mapping=dict(x=Service))
    def h(x, b=1):
        return x

    assert container[Service] is h()

    manager.mapping = dict(x=Service, y=Service)

    @manager.inject
    def u(x):
        return x

    assert container[Service] is u()

    @manager.inject(mapping=dict(y=AnotherService))
    def v(x, y):
        return x, y

    assert container[Service] is v()[0]
    assert container[AnotherService] is v()[1]


def test_wire():
    manager = DependencyManager()
    container = manager.container

    class Service(object):
        pass

    class AnotherService(object):
        pass

    manager.register(Service)
    manager.register(AnotherService)

    @manager.wire(mapping=dict(service=Service,
                               another_service=AnotherService))
    class Something(object):
        def f(self, service):
            return service

        def g(self, another_service):
            return another_service

        def h(self, service, another_service):
            return service, another_service

        def u(self):
            pass

        def v(self, nothing):
            return nothing

    something = Something()
    assert container[Service] is something.f()
    assert container[AnotherService] is something.g()

    s1, s2 = something.h()
    assert container[Service] is s1
    assert container[AnotherService] is s2

    something.u()

    with pytest.raises(TypeError):
        something.v()


def test_use_names():
    manager = DependencyManager(use_names=False)
    container = manager.container

    _service = object()
    _service_bis = object()
    container['service'] = _service
    container['service_bis'] = _service_bis

    def f(service):
        return service

    with pytest.raises(TypeError):
        manager.inject(f)()

    def g(service, service_bis=None, something=None):
        return service, service_bis, something

    g_result = manager.inject(use_names=True)(g)()
    assert _service is g_result[0]
    assert _service_bis is g_result[1]
    assert None is g_result[2]

    g_result = manager.inject(use_names=('service',))(g)()
    assert _service is g_result[0]
    assert None is g_result[1]
    assert None is g_result[2]

    # use names for every injection by default.
    manager.use_names = True

    assert _service is manager.inject(f)()

    with pytest.raises(TypeError):
        manager.inject(use_names=False)(f)()


def test_register():
    manager = DependencyManager(auto_wire=True)
    container = manager.container

    @manager.register
    class Service(object):
        pass

    assert isinstance(container[Service], Service)

    @manager.register(mapping=dict(service=Service))
    class AnotherService(object):
        def __init__(self, service):
            self.service = service

    assert isinstance(container[AnotherService], AnotherService)
    assert container[Service] is container[AnotherService].service
    # singleton
    assert container[AnotherService] is container[AnotherService]

    container['service'] = object()

    @manager.register(use_names=True)
    class YetAnotherService(object):
        def __init__(self, service):
            self.service = service

    assert isinstance(container[YetAnotherService], YetAnotherService)
    assert container['service'] is container[YetAnotherService].service
    # singleton
    assert container[YetAnotherService] is container[YetAnotherService]

    @manager.register(singleton=False)
    class SingleUsageService(object):
        pass

    assert isinstance(container[SingleUsageService], SingleUsageService)
    assert container[SingleUsageService] is not container[SingleUsageService]

    @manager.register(auto_wire=False)
    class BrokenService(object):
        def __init__(self, service):
            self.service = service

    with pytest.raises(DependencyInstantiationError):
        container[BrokenService]

    @manager.register(auto_wire=('__init__', 'method'),
                      mapping=dict(service=Service,
                                   x=SingleUsageService,
                                   yet=YetAnotherService))
    class ComplexWiringService(object):
        def __init__(self, service):
            self.service = service

        def method(self, x, yet):
            return x, yet

    assert isinstance(container[ComplexWiringService], ComplexWiringService)
    assert container[Service] is container[ComplexWiringService].service
    output = container[ComplexWiringService].method()

    assert isinstance(output[0], SingleUsageService)
    assert output[1] is container[YetAnotherService]


def test_register_non_class():
    manager = DependencyManager()

    with pytest.raises(ValueError):
        manager.register(object())

    def f():
        pass

    with pytest.raises(ValueError):
        manager.register(f)


def test_factory_function():
    manager = DependencyManager()
    container = manager.container

    class Service(object):
        pass

    with pytest.raises(ValueError):
        @manager.factory
        def faulty_service_provider():
            return Service()

    @manager.factory(dependency_id=Service)
    def service_provider():
        return Service()

    assert isinstance(container[Service], Service)
    # is a singleton
    assert container[Service] is container[Service]

    class AnotherService(object):
        def __init__(self, service):
            self.service = service

    @manager.factory(mapping=dict(service=Service),
                     dependency_id=AnotherService)
    def another_service_provider(service):
        return AnotherService(service)

    assert isinstance(container[AnotherService], AnotherService)
    # is a singleton
    assert container[AnotherService] is container[AnotherService]
    assert isinstance(container[AnotherService].service, Service)

    s = object()
    container['test'] = s

    class YetAnotherService:
        pass

    @manager.factory(use_names=True, dependency_id=YetAnotherService)
    def injected_by_name_provider(test):
        return test

    assert s is container[YetAnotherService]

    with pytest.raises(ValueError):
        manager.factory(1)

    with pytest.raises(ValueError):
        @manager.factory
        class Test:
            pass


def test_factory_class():
    manager = DependencyManager()
    container = manager.container

    class Service(object):
        pass

    with pytest.raises(ValueError):
        @manager.factory
        class FaultyServiceProvider(object):
            def __call__(self):
                return Service()

    @manager.factory(dependency_id=Service)
    class ServiceProvider(object):
        def __call__(self):
            return Service()

    assert isinstance(container[Service], Service)
    # is a singleton
    assert container[Service] is container[Service]

    class AnotherService(object):
        def __init__(self, service):
            self.service = service

    @manager.factory(mapping=dict(service=Service),
                     dependency_id=AnotherService)
    class AnotherServiceProvider(object):
        def __init__(self, service):
            self.service = service
            assert isinstance(service, Service)

        def __call__(self, service):
            assert self.service is service
            return AnotherService(service)

    assert isinstance(container[AnotherService], AnotherService)
    # is a singleton
    assert container[AnotherService] is container[AnotherService]
    assert isinstance(container[AnotherService].service, Service)

    container['test'] = object()

    class YetAnotherService(object):
        pass

    @manager.factory(use_names=True, dependency_id=YetAnotherService)
    class YetAnotherServiceProvider(object):
        def __init__(self, test):
            self.test = test

        def __call__(self, test):
            assert self.test is test
            return test

    assert container['test'] is container[YetAnotherService]

    class OtherService(object):
        pass

    @manager.factory(use_names=True,
                     mapping=dict(service=Service),
                     auto_wire=('__init__',),
                     dependency_id=OtherService)
    class OtherServiceProvider(object):
        def __init__(self, test, service):
            self.test = test
            self.service = service

        def __call__(self):
            return self.test, self.service

    output = container[OtherService]
    assert output[0] is container['test']
    assert isinstance(output[1], Service)


def test_provider():
    manager = DependencyManager()
    container = manager.container

    container['service'] = object()

    @manager.provider(use_names=True)
    class DummyProvider(object):
        def __init__(self, service=None):
            self.service = service

        def __antidote_provide__(self, dependency_id):
            if dependency_id == 'test':
                return Dependency(dependency_id)
            else:
                raise DependencyNotProvidableError(dependency_id)

    assert isinstance(container.providers[DummyProvider], DummyProvider)
    assert container.providers[DummyProvider].service is container['service']
    assert 'test' == container['test']

    with pytest.raises(DependencyNotFoundError):
        container['test2']

    with pytest.raises(ValueError):
        manager.provider(object())

    with pytest.raises(ValueError):
        @manager.provider
        class MissingAntidoteProvideMethod(object):
            pass

    with pytest.raises(TypeError):
        @manager.provider(auto_wire=False)
        class MissingDependencyProvider(object):
            def __init__(self, service):
                self.service = service

            def __antidote_provide__(self, dependency_id):
                return Dependency(dependency_id)


def test_provider_ignore_excess_arguments():
    manager = DependencyManager()
    container = manager.container

    @manager.provider
    class DummyProvider(object):
        def __antidote_provide__(self, dependency_id):
            return Dependency(dependency_id)

    s = object()
    assert s is container.provide(s, 1, 2)
    assert s is container.provide(s, random=1)
    assert s is container.provide(s, 1, another=1)


def test_provider_ignore_excess_arguments_2a():
    manager = DependencyManager()
    container = manager.container

    @manager.provider
    class DummyProvider(object):
        def __antidote_provide__(self, dependency_id, param=None):
            return Dependency((dependency_id, param))

    s = object()
    assert (s, 1) == container.provide(s, 1)
    assert (s, 1) == container.provide(s, 1, 2, 3)
    assert (s, 1) == container.provide(s, param=1)
    assert (s, None) == container.provide(s, random=1)


def test_provider_ignore_excess_arguments_2b():
    manager = DependencyManager()
    container = manager.container

    @manager.provider
    class DummyProvider(object):
        def __antidote_provide__(self, dependency_id, param=None, *args):
            return Dependency((dependency_id, param, args))

    s = object()
    assert (s, 1, tuple()) == container.provide(s, 1)
    assert (s, 1, (2,)) == container.provide(s, 1, 2)
    assert (s, 1, tuple()) == container.provide(s, param=1)
    assert (s, None, tuple()) == container.provide(s, random=1)


def test_provider_ignore_excess_arguments_2c():
    manager = DependencyManager()
    container = manager.container

    @manager.provider
    class DummyProvider(object):
        def __antidote_provide__(self, dependency_id, param=None, **kwargs):
            return Dependency((dependency_id, param, kwargs))

    s = object()
    assert (s, 1, {}) == container.provide(s, 1)
    assert (s, 1, {}) == container.provide(s, param=1)
    assert (s, 1, {'test': 2}) == container.provide(s, param=1, test=2)
    assert (s, None, {'random': 1}) == container.provide(s, random=1)


def test_provider_ignore_excess_arguments_3():
    manager = DependencyManager()
    container = manager.container

    @manager.provider
    class DummyProvider(object):
        def __antidote_provide__(self, dependency_id, *args, **kwargs):
            return Dependency((dependency_id, args, kwargs))

    s = object()
    assert (s, (1,), {}) == container.provide(s, 1)
    assert (s, tuple(), {'random': 1}) == container.provide(s, random=1)
    assert (s, (1,), {'random': 1}) == container.provide(s, 1, random=1)
