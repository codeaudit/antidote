# cython: language_level=3, boundscheck=False, wraparound=False
import collections.abc as c_abc
import typing
from typing import (Callable, Iterable, Mapping, Union)

# @formatter:off
cimport cython
from libcpp cimport bool as cbool

from .._internal.argspec import get_arguments_specification
from .._internal.container import get_global_container
# noinspection PyUnresolvedReferences
from ..container cimport DependencyContainer, DependencyContainer, Instance
# @formatter:on

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

    def _inject(f):
        # _generate_injection_blueprint(
        #         func=f,
        #         arg_map=arg_map,
        #         use_names=use_names,
        #         use_type_hints=use_type_hints
        #     )
        # return f
        return InjectedCallableWrapper(
            container=container or get_global_container(),
            blueprint=_generate_injection_blueprint(
                func=f,
                arg_map=arg_map,
                use_names=use_names,
                use_type_hints=use_type_hints
            ),
            wrapped=f
        )

    return func and _inject(func) or _inject

cdef class InjectedCallableWrapper:
    cdef:
        object __wrapped__
        DependencyContainer __container__
        InjectionBlueprint __blueprint__

    def __init__(self,
                 DependencyContainer container,
                 InjectionBlueprint blueprint,
                 object wrapped):
        self.__container__ = container
        self.__wrapped__ = wrapped
        self.__blueprint__ = blueprint

    def __call__(self, *args, **kwargs):
        kwargs = _inject_kwargs(self.__container__, self.__blueprint__, args, kwargs)
        return self.__wrapped__(*args, **kwargs)

    def __get__(self, instance, owner):
        func = self.__wrapped__.__get__(instance, owner)
        return InjectedBoundCallableWrapper(self.__container__, self.__blueprint__,
                                            func)

cdef class InjectedBoundCallableWrapper(InjectedCallableWrapper):
    def __get__(self, instance, owner):
        return self

cdef class InjectionBlueprint:
    cdef:
        tuple injections

    def __init__(self, tuple injections):
        self.injections = injections

@cython.freelist(5)
cdef class Injection:
    cdef:
        str arg_name
        cbool required
        object dependency_id

    def __init__(self, str arg_name, cbool required, object dependency_id):
        self.arg_name = arg_name
        self.required = required
        self.dependency_id = dependency_id

cdef dict _inject_kwargs(DependencyContainer container,
                         InjectionBlueprint blueprint,
                         tuple args,
                         dict kwargs):
    cdef:
        Injection injection
        object instance
        cbool dirty_kwargs = False

    for injection in blueprint.injections[len(args):]:
        if injection.dependency_id is not None and injection.arg_name not in kwargs:
            instance = container.provide(injection.dependency_id)
            if instance is not None:
                if not dirty_kwargs:
                    kwargs = kwargs.copy()
                    dirty_kwargs = True
                kwargs[injection.arg_name] = instance

    return kwargs

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

    type_hints = None
    if use_type_hints is not False:
        try:
            type_hints = typing.get_type_hints(func)
        except Exception:
            # Python 3.5.3 does not handle properly method wrappers
            pass
    type_hints = type_hints or dict()

    if isinstance(use_type_hints, c_abc.Iterable):
        type_hints = {arg_name: type_hint
                      for arg_name, type_hint in type_hints.items()
                      if arg_name in use_type_hints}
    elif use_type_hints is not True and use_type_hints is not False:
        raise ValueError('Only an iterable or a boolean is supported for '
                         'use_type_hints, not {!r}'.format(use_names))

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

    arg_to_dependency = {k: v
                         for k, v in arg_to_dependency.items()
                         if v is not None}

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
        # Injection(arg_name=arg.name,
        #           required=not arg.has_default,
        #           dependency_id=dependency_id)
        # if dependency_id is not None else
        None
        for arg, dependency_id in zip(arg_spec.arguments, dependencies)
    ]))
