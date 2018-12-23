import inspect
from typing import Callable, Iterable, Union

from .inject import ARG_MAP_TYPE, inject
from ..container import DependencyContainer


def wire(class_: type = None,
         *,
         methods: Iterable[str] = None,
         arg_map: ARG_MAP_TYPE = None,
         use_names: Union[bool, Iterable[str]] = None,
         use_type_hints: Union[bool, Iterable[str]] = None,
         container: DependencyContainer = None
         ) -> Union[Callable, type]:
    """Wire a class by injecting the dependencies in all specified methods.

    Args:
        class_: class to wire.
        methods: Name of the methods for which dependencies should be
            injected. Defaults to all defined methods.
        arg_map: Can be either a mapping of arguments name to their dependency
            id, an iterable of dependency ids or a function which returns the
            dependency ID for an arguments name. If an iterable is specified,
            the position of the arguments is used to determine their
            respective dependency. An argument may be skipped by using
            :code:`None` as as placeholder. Type hints are overridden. Defaults
            to :code:`None`.
        use_names: Whether or not the arguments' name should be used as
            dependency ids. An iterable of argument names may also be
            supplied to restrict this to those. Defaults to :code:`False`.
        use_type_hints: Whether or not the type hints (annotations) should be
            used as dependency ids. An iterable of argument names may also be
            supplied to restrict this to those. Any type hints from the
            builtins (str, int...) or the typing (:py:class:`~typing.Optional`,
            ...) are ignored. Defaults to :code:`True`.
        container: :py:class:~.container.base.DependencyContainer` from which
            the dependencies should be retrieved. Defaults to the global
            container if it is defined.

    Returns:
        Wired class or a decorator.

    """

    def wire_methods(cls):
        if not inspect.isclass(cls):
            raise ValueError("Expecting a class, got a {}".format(type(cls)))

        nonlocal methods

        if methods is None:
            methods = map(
                lambda m: m[0],  # get only the name
                inspect.getmembers(
                    cls,
                    # Retrieve static methods, class methods, methods.
                    predicate=lambda f: (inspect.isfunction(f)
                                         or inspect.ismethod(f))
                )
            )

        for method in methods:
            setattr(cls,
                    method,
                    inject(getattr(cls, method),
                           arg_map=arg_map,
                           use_names=use_names,
                           use_type_hints=use_type_hints,
                           container=container))

        return cls

    return class_ and wire_methods(class_) or wire_methods
