import pytest

from antidote import (DependencyContainer, FactoryProvider, GetterProvider, TagProvider)
from antidote.helpers import factory, getter, register
from antidote.injection import inject, wire


class Service:
    pass


class AnotherService:
    pass


class YetAnotherService:
    pass


class SuperService:
    pass


@pytest.fixture()
def container():
    c = DependencyContainer()
    c.providers[FactoryProvider] = FactoryProvider()
    c.providers[GetterProvider] = GetterProvider()
    c.providers[TagProvider] = TagProvider(container=c)

    c.update({cls: cls() for cls in [Service, AnotherService, YetAnotherService]})
    c.update(dict(service=object(),
                  another_service=object()))

    return c


class DummyMixin:
    def method(self, yet_another_service: YetAnotherService):
        return yet_another_service


class MyService(DummyMixin):
    def __init__(self,
                 service: Service,
                 another_service=None):
        self.service = service
        self.another_service = another_service


class C1(DummyMixin):
    def __init__(self,
                 service: Service,
                 another_service=None):
        self.service = service
        self.another_service = another_service

    def __call__(self) -> MyService:
        return MyService(self.service, self.another_service)


class C2(DummyMixin):
    def __init__(self, service: Service):
        self.service = service

    def __call__(self, another_service=None) -> MyService:
        return MyService(self.service, another_service)


class C3(DummyMixin):
    def __call__(self,
                 service: Service,
                 another_service=None) -> MyService:
        return MyService(service, another_service)


def f1(service: Service, another_service=None) -> MyService:
    return MyService(service, another_service)


def wire_(class_=None, auto_wire=True, **kwargs):
    if auto_wire is True:
        m = None
    elif auto_wire is False:
        m = []
    else:
        m = auto_wire

    return wire(class_=class_, methods=m, **kwargs)


wire_.__name__ = 'wire'


class_one_inj_tests = [
    [wire_, MyService],
    [wire_, C1],
    [wire_, C3],
    [register, MyService],
    [factory, C1],
    [factory, C3],
    [getter, C1],
    [getter, C3],
]

class_two_inj_tests = [
    [wire_, C2],
    [factory, C2],
    [getter, C2],
]

class_tests = class_one_inj_tests + class_two_inj_tests

function_tests = [
    [factory, f1],
    [getter, f1],
    [inject, f1],
]

all_tests = class_tests + function_tests


def parametrize_injection(tests, lazy=False, call_if_callable_class=True,
                          **inject_kwargs):
    def decorator(test):
        @pytest.mark.parametrize('wrapper,wrapped', tests)
        def f(container, wrapper, wrapped):
            if isinstance(wrapped, type):
                # helpers do modify the class, so a copy has to be made to
                # avoid any conflict between the tests.
                wrapped = type(wrapped.__name__,
                               wrapped.__bases__,
                               wrapped.__dict__.copy())

            def create():
                instance = wrapper(container=container, **inject_kwargs)(wrapped)()
                if isinstance(wrapped, type) and call_if_callable_class:
                    # Factory classes are callable
                    return instance() if callable(instance) else instance
                return instance

            if lazy:
                return test(container,
                            create_instance=create)

            return test(container, instance=create())

        return f

    return decorator


@parametrize_injection(all_tests)
def test_basic_wiring(container, instance: MyService):
    assert instance.service is container[Service]
    assert instance.another_service is None


@parametrize_injection(class_tests, call_if_callable_class=False,
                       auto_wire=['__init__', 'method'])
def test_complex_wiring(container, instance: DummyMixin):
    assert instance.method() is container[YetAnotherService]


@parametrize_injection(class_tests, lazy=True, auto_wire=False)
def test_no_wiring(container, create_instance):
    with pytest.raises(TypeError):
        create_instance()


@parametrize_injection(all_tests, lazy=True, use_type_hints=False)
def test_no_type_hints(container, create_instance):
    with pytest.raises(TypeError):
        create_instance()


@parametrize_injection(all_tests, use_type_hints=['service'])
def test_type_hints_only_service(container, instance):
    assert instance.service is container[Service]
    assert instance.another_service is None


@parametrize_injection(all_tests, lazy=True,
                       use_type_hints=['another_service'])
def test_type_hints_only_another_service(container, create_instance):
    with pytest.raises(TypeError):
        create_instance()


@parametrize_injection(all_tests,
                       arg_map=dict(service=AnotherService))
def test_arg_map_dict_override(container, instance: MyService):
    assert instance.service is container[AnotherService]
    assert instance.another_service is None


@parametrize_injection(all_tests,
                       arg_map=dict(another_service=AnotherService))
def test_arg_map_dict(container, instance: MyService):
    assert instance.service is container[Service]
    assert instance.another_service is container[AnotherService]


@parametrize_injection(class_one_inj_tests, arg_map=(None, AnotherService))
def test_class_arg_map_tuple_override(container, instance: MyService):
    assert instance.service is container[AnotherService]
    assert instance.another_service is None


@parametrize_injection(function_tests, arg_map=(AnotherService,))
def test_function_arg_map_tuple_override(container, instance: MyService):
    assert instance.service is container[AnotherService]
    assert instance.another_service is None


@parametrize_injection(class_one_inj_tests, arg_map=(None, None, AnotherService))
def test_class_arg_map_tuple(container, instance: MyService):
    assert instance.service is container[Service]
    assert instance.another_service is container[AnotherService]


@parametrize_injection(function_tests, arg_map=(None, AnotherService))
def test_function_arg_map_tuple(container, instance: MyService):
    assert instance.service is container[Service]
    assert instance.another_service is container[AnotherService]


@parametrize_injection(all_tests, use_names=True)
def test_use_names_activated(container, instance: MyService):
    assert instance.service is container[Service]
    assert instance.another_service is container['another_service']


@parametrize_injection(all_tests, use_names=['another_service'])
def test_use_names_only_another_service(container, instance: MyService):
    assert instance.service is container[Service]
    assert instance.another_service is container['another_service']


@parametrize_injection(all_tests, use_names=['service'])
def test_use_names_only_service(container, instance: MyService):
    assert instance.service is container[Service]
    assert instance.another_service is None
