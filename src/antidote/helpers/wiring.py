import collections.abc as c_abc
import inspect
from typing import Any, Callable, Iterable, Mapping, Union

from .._internal.argspec import Arguments
from ..core import DependencyContainer, inject

LIMITED_DEPENDENCIES_TYPE = Union[Mapping[str, Any], Callable[[str], Any], str]


def wire(class_: type = None,
         *,
         methods: Iterable[str] = None,
         dependencies: LIMITED_DEPENDENCIES_TYPE = None,
         use_names: Union[bool, Iterable[str]] = None,
         use_type_hints: Union[bool, Iterable[str]] = None,
         container: DependencyContainer = None
         ) -> Union[Callable, type]:
    """Wire a class by injecting the dependencies in all specified methods.

    Args:
        class_: class to wire.
        methods: Name of the methods for which dependencies should be
            injected. Defaults to all defined methods.
        dependencies: Can be either a mapping of arguments name to their
            dependency, an iterable of dependencies or a function which returns
            the dependency given the arguments name. If an iterable is specified,
            the position of the arguments is used to determine their respective
            dependency. An argument may be skipped by using :code:`None` as a
            placeholder. Type hints are overridden. Defaults to :code:`None`.
        use_names: Whether or not the arguments' name should be used as their
            respective dependency. An iterable of argument names may also be
            supplied to restrict this to those. Defaults to :code:`False`.
        use_type_hints: Whether or not the type hints (annotations) should be
            used as the arguments dependency. An iterable of argument names may
            also be specified to restrict this to those. Any type hints from
            the builtins (str, int...) or the typing (:py:class:`~typing.Optional`,
            ...) are ignored. Defaults to :code:`True`.
        container: :py:class:~.core.base.DependencyContainer` from which
            the dependencies should be retrieved. Defaults to the global
            core if it is defined.

    Returns:
        Wired class or a decorator.

    """

    def wire_methods(cls):
        nonlocal methods

        if not inspect.isclass(cls):
            raise ValueError("Expecting a class, got a {}".format(type(cls)))

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
        elif isinstance(methods, c_abc.Iterable):
            methods = tuple(methods)
        else:
            raise ValueError("methods must be either None or an iterable.")

        if isinstance(dependencies, c_abc.Iterable) \
                and not isinstance(dependencies, c_abc.Mapping) \
                and len(methods) > 1:
            raise ValueError("wire does not support an iterable for `dependencies` "
                             "when multiple methods are injected.")

        for method_name in methods:
            try:
                wrapped = cls.__dict__[method_name]
            except KeyError:
                continue

            _dependencies = dependencies
            _use_names = use_names
            _use_type_hints = use_type_hints

            if isinstance(dependencies, dict) \
                    or isinstance(use_names, c_abc.Iterable) \
                    or isinstance(use_type_hints, c_abc.Iterable):
                arguments = Arguments.from_callable(
                    wrapped.__func__
                    if isinstance(wrapped, (staticmethod, classmethod)) else
                    wrapped
                )

                if isinstance(dependencies, dict):
                    _dependencies = {
                        arg_name: dependency
                        for arg_name, dependency in dependencies.items()
                        if arg_name in arguments
                    }
                    if not _dependencies:
                        _dependencies = None

                if isinstance(use_names, c_abc.Iterable):
                    _use_names = [name
                                  for name in use_names
                                  if name in arguments]
                    if not _use_names:
                        _use_names = False

                if isinstance(use_type_hints, c_abc.Iterable):
                    _use_type_hints = [name
                                       for name in use_type_hints
                                       if name in arguments]
                    if not _use_type_hints:
                        _use_type_hints = False

            setattr(cls,
                    method_name,
                    inject(wrapped,
                           dependencies=_dependencies,
                           use_names=_use_names,
                           use_type_hints=_use_type_hints,
                           container=container))

        return cls

    return class_ and wire_methods(class_) or wire_methods
