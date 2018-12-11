import collections.abc as c_abc
import typing
from functools import WRAPPER_ASSIGNMENTS
from typing import (Callable, Iterable, Mapping, Union)

from .wrapper import InjectedCallableWrapper, Injection, InjectionBlueprint
from .._internal.argspec import get_arguments_specification
from .._internal.global_container import get_global_container
from ..container import DependencyContainer


def inject(func: Callable = None,
           arg_map: Union[Mapping, Iterable] = None,
           use_names: Union[bool, Iterable[str]] = None,
           use_type_hints: Union[bool, Iterable[str]] = None,
           container: DependencyContainer = None
           ) -> Callable:
    """
    Inject the dependency into the function lazily: they are only
    retrieved upon execution.

    Args:
        func: Callable for which the argument should be injected.
        arg_map: Custom mapping of the arguments name to their respective
            dependency id. A sequence of dependencies can also be
            specified, which will be mapped to the arguments through their
            order. Annotations are overridden.
        use_names: Whether the arguments name should be used to find for
            a dependency. An iterable of names may also be provided to
            restrict this to a subset of the arguments. Annotations are
            overridden, but not the arg_map.
        use_type_hints: Whether the type hints should be used to find for
            a dependency. An iterable of names may also be provided to
            restrict this to a subset of the arguments.
        container: :py:class:~.container.base.DependencyContainer` from which
            the dependencies should be retrieved. Defaults to the global
            container if it is defined.

    Returns:
        The decorator to be applied or the injected function if the
        argument :code:`func` was supplied.

    """

    def _inject(wrapped):
        if isinstance(wrapped, InjectedCallableWrapper):
            return wrapped
        wrapper = InjectedCallableWrapper(
            container=container or get_global_container(),
            blueprint=_generate_injection_blueprint(
                func=wrapped,
                arg_map=arg_map,
                use_names=use_names,
                use_type_hints=use_type_hints
            ),
            wrapped=wrapped
        )
        for attr in WRAPPER_ASSIGNMENTS:
            try:
                value = getattr(wrapper, attr)
            except AttributeError:
                pass
            else:
                setattr(wrapper, attr, value)

        return wrapper

    return func and _inject(func) or _inject


def _generate_injection_blueprint(func: Callable,
                                  arg_map: Union[Mapping, Iterable] = None,
                                  use_names: Union[bool, Iterable[str]] = None,
                                  use_type_hints: Union[bool, Iterable[str]] = None,
                                  ) -> InjectionBlueprint:
    """
    Construct a list with all the necessary information about the arguments
    for dependency injection, named the injection blueprint. Storing it
    avoids significant execution overhead.
    """
    use_names = use_names if use_names is not None else False
    use_type_hints = use_type_hints if use_type_hints is not None else True

    arg_spec = get_arguments_specification(func)

    if arg_map is None:
        arg_to_dependency = {}  # type: Mapping
    elif isinstance(arg_map, c_abc.Mapping):
        arg_to_dependency = arg_map
    elif isinstance(arg_map, c_abc.Iterable):
        arg_to_dependency = {arg.name: dependency_id
                             for arg, dependency_id
                             in zip(arg_spec.arguments, arg_map)}
    else:
        raise ValueError('Only a mapping or a iterable is supported for '
                         'arg_map, not {!r}'.format(arg_map))

    # Remove any None as they would hide type_hints and use_names.
    arg_to_dependency = {k: v
                         for k, v in arg_to_dependency.items()
                         if v is not None}

    type_hints = None
    if use_type_hints is not False:
        try:
            type_hints = typing.get_type_hints(func)
        except Exception:  # Python 3.5.3 does not handle properly method wrappers
            pass
    type_hints = type_hints or dict()

    if isinstance(use_type_hints, c_abc.Iterable):
        type_hints = {arg_name: type_hint
                      for arg_name, type_hint in type_hints.items()
                      if arg_name in use_type_hints}
    elif use_type_hints is not True and use_type_hints is not False:
        raise ValueError('Only an iterable or a boolean is supported for '
                         'use_type_hints, not {!r}'.format(use_names))

    # Any object from builtins or typing do not carry any useful information
    # and thus must not be used as dependency IDs. So they might as well be
    # skipped entirely. Moreover they hide use_names.
    type_hints = {
        arg_name: type_hint
        for arg_name, type_hint in type_hints.items()
        if getattr(type_hint, '__module__', '') not in {'typing', 'builtins'}
    }

    if use_names is False:
        use_names = set()
    elif use_names is True:
        use_names = set(arg.name for arg in arg_spec.arguments)
    elif isinstance(use_names, c_abc.Iterable):
        use_names = set(use_names)
    else:
        raise ValueError('Only an iterable or a boolean is supported for '
                         'use_names, not {!r}'.format(use_names))

    dependencies = [
        arg_to_dependency.get(
            arg.name,
            type_hints.get(arg.name, arg.name if arg.name in use_names else None)
        )
        for arg in arg_spec.arguments
    ]

    return InjectionBlueprint(tuple([
        Injection(arg_name=arg.name,
                  required=not arg.has_default,
                  dependency_id=dependency_id)
        for arg, dependency_id in zip(arg_spec.arguments, dependencies)
    ]))
