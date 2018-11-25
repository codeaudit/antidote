import pytest

from antidote import DependencyNotProvidableError, Instance
from antidote.exceptions import GetterNamespaceConflict
from antidote.providers.getters import Dependency, GetterProvider


def test_repr():
    provider = GetterProvider()

    def getter(_):
        pass

    provider.register(getter=getter, namespace='')

    assert str(getter) in repr(provider)


def test_simple_getter():
    provider = GetterProvider()

    data = dict(y=object(), x=object())

    def getter(key):
        return data[key]

    provider.register(getter=getter, namespace='')

    assert isinstance(provider.__antidote_provide__(Dependency('y')), Instance)
    assert data['y'] == provider.__antidote_provide__(Dependency('y')).item
    assert data['x'] == provider.__antidote_provide__(Dependency('x')).item

    with pytest.raises(DependencyNotProvidableError):
        provider.__antidote_provide__(Dependency('z'))


def test_namespace():
    provider = GetterProvider()

    expected_1 = object()
    expected_2 = object()

    provider.register(getter=lambda _: expected_1, namespace='g1')
    provider.register(getter=lambda _: expected_2, namespace='g2')

    assert expected_1 == provider.__antidote_provide__(Dependency('g1:test')).item
    assert expected_2 == provider.__antidote_provide__(Dependency('g2:test')).item

    with pytest.raises(DependencyNotProvidableError):
        provider.__antidote_provide__(Dependency('g3:test'))


def test_omit_namespace():
    provider = GetterProvider()

    data = dict(y=object(), x=object())

    def getter(key):
        return data[key]

    def raiser(_):
        raise Exception()

    provider.register(getter=getter, namespace='conf:', omit_namespace=True)
    provider.register(getter=raiser, namespace='test:', omit_namespace=True)

    assert data['y'] == provider.__antidote_provide__(Dependency('conf:y')).item
    assert data['x'] == provider.__antidote_provide__(Dependency('conf:x')).item


def test_invalid_namespace():
    provider = GetterProvider()
    with pytest.raises(ValueError):
        provider.register(lambda _: None, namespace=object())


def test_namespace_conflict():
    provider = GetterProvider()

    provider.register(lambda _: None, namespace='test')

    with pytest.raises(GetterNamespaceConflict):
        provider.register(lambda _: None, namespace='test2')

    with pytest.raises(GetterNamespaceConflict):
        provider.register(lambda _: None, namespace='test')

    with pytest.raises(GetterNamespaceConflict):
        provider.register(lambda _: None, namespace='tes')


def test_singleton():
    provider = GetterProvider()

    provider.register(lambda _: object(), namespace='default')
    assert True is provider.__antidote_provide__(Dependency('default')).singleton

    provider.register(lambda _: object(), namespace='singleton', singleton=True)
    assert True is provider.__antidote_provide__(Dependency('singleton')).singleton

    provider.register(lambda _: object(), namespace='unique', singleton=False)
    assert False is provider.__antidote_provide__(Dependency('unique')).singleton


