"""
Test only that the wrapper behaves nicely in all cases.
Injection itself is tested through inject.
"""
import pytest

from antidote import DependencyContainer
from antidote._internal.wrapper import InjectedWrapper, InjectionBlueprint

container = DependencyContainer()
blueprint = InjectionBlueprint(tuple())
sentinel = object()


def wrap(func):
    return InjectedWrapper(
        container=container,
        blueprint=blueprint,
        wrapped=func
    )


class Dummy:
    @wrap
    def method(self, x):
        return self, x

    @wrap
    @classmethod
    def class_before(cls, x):
        return cls, x

    @classmethod
    @wrap
    def class_after(cls, x):
        return cls, x

    @wrap
    @staticmethod
    def static_before(x):
        return x

    @staticmethod
    @wrap
    def static_after(x):
        return x


class Dummy2:
    def method(self, x):
        return self, x

    @classmethod
    def class_method(cls, x):
        return cls, x

    @staticmethod
    def static(x):
        return x


Dummy2.method = wrap(Dummy2.__dict__['method'])
Dummy2.class_method = wrap(Dummy2.__dict__['class_method'])
Dummy2.static = wrap(Dummy2.__dict__['static'])


@wrap
def f(x):
    return x


d = Dummy()
d2 = Dummy2()


@pytest.mark.parametrize(
    'expected, func',
    [
        pytest.param(sentinel, f,
                     id='func'),

        pytest.param((sentinel, sentinel), Dummy.method,
                     id='method'),
        pytest.param((Dummy, sentinel), Dummy.class_before,
                     id='classmethod before'),
        pytest.param((Dummy, sentinel), Dummy.class_after,
                     id='classmethod after'),
        pytest.param(sentinel, Dummy.static_before,
                     id='staticmethod before'),
        pytest.param(sentinel, Dummy.static_after,
                     id='staticmethod after'),

        pytest.param((d, sentinel), d.method,
                     id='instance method'),
        pytest.param((Dummy, sentinel), d.class_before,
                     id='instance classmethod before'),
        pytest.param((Dummy, sentinel), d.class_after,
                     id='instance classmethod after'),
        pytest.param(sentinel, d.static_before,
                     id='instance staticmethod before'),
        pytest.param(sentinel, d.static_after,
                     id='instance staticmethod after'),

        pytest.param((d2, sentinel), d2.method,
                     id='post:instance method'),
        pytest.param((Dummy2, sentinel), d2.class_method,
                     id='post:instance classmethod'),
        pytest.param(sentinel, d2.static,
                     id='post:instance staticmethod'),

        pytest.param((sentinel, sentinel), Dummy2.method,
                     id='post:method'),
        pytest.param((Dummy2, sentinel), Dummy2.class_method,
                     id='post:classmethod'),
        pytest.param(sentinel, Dummy2.static,
                     id='post:staticmethod'),
    ]
)
def test_wrapper(expected, func):
    if expected == (sentinel, sentinel):
        assert expected == func(sentinel, sentinel)
    else:
        assert expected == func(sentinel)
