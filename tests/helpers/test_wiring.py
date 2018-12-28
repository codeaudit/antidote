import pytest

from antidote import wire
from antidote.core import DependencyContainer


def test_invalid_class():
    with pytest.raises(ValueError):
        wire(object())

    with pytest.raises(ValueError):
        wire(1)

    with pytest.raises(ValueError):
        wire(lambda: None)


def test_invalid_methods():
    with pytest.raises(ValueError):
        @wire(methods=object())
        class Dummy:
            pass


def test_invalid_dependencies_with_multiple_methods():
    with pytest.raises(ValueError):
        @wire(methods=['__ini__', '__call__'], dependencies=(None, None))
        class Dummy:
            pass


def test_complex_wire():
    container = DependencyContainer()
    xx = object()
    yy = object()
    container.update_singletons(dict(x=xx, y=yy))

    @wire(methods=['f', 'g'],
          dependencies=dict(x='x', y='y'),
          container=container)
    class Dummy:
        def f(self, x):
            return x

        def g(self, x, y):
            return x, y

    d1 = Dummy()
    assert xx == d1.f()
    assert (xx, yy) == d1.g()

    @wire(methods=['f', 'g'],
          use_names=['x', 'y'],
          container=container)
    class Dummy2:
        def f(self, x):
            return x

        def g(self, x, y):
            return x, y

    d2 = Dummy2()
    assert xx == d2.f()
    assert (xx, yy) == d2.g()

    container.update_singletons({Dummy: d1, Dummy2: d2})

    @wire(methods=['f', 'g'],
          use_type_hints=['x', 'y'],
          container=container)
    class Dummy3:
        def f(self, x: Dummy):
            return x

        def g(self, x: Dummy, y: Dummy2):
            return x, y

    assert d1 == Dummy3().f()
    assert (d1, d2) == Dummy3().g()
