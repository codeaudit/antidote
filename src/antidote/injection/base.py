import collections.abc as c_abc
import typing
from itertools import islice
from typing import (Callable, Dict, Iterable, Mapping, Optional, Sequence,
                    Tuple, Union)

import wrapt

from .._internal.argspec import get_arguments_specification
from .._internal.utils import SlotReprMixin
from ..container import DependencyContainer
from ..exceptions import DependencyNotFoundError, UndefinedContainerError


class Injection(SlotReprMixin):
    __slots__ = ('arg_name', 'required', 'dependency_id')

    def __init__(self, arg_name: str, required: bool, dependency_id):
        self.arg_name = arg_name
        self.required = required
        self.dependency_id = dependency_id


class InjectionBlueprint(SlotReprMixin):
    __slots__ = ('injections',)

    def __init__(self, injections: Sequence[Optional[Injection]]):
        self.injections = injections


class Injector(SlotReprMixin):
    __slots__ = ('container', 'blueprint')

    def __init__(self, container, blueprint):
        self.container = container
        self.blueprint = blueprint

    def __call__(self, wrapped, instance, args, kwargs):
        args, kwargs = _generate_args_kwargs(
            self.container,
            self.blueprint,
            args,
            kwargs,
            skip_first=instance is not None
        )

        return wrapped(*args, **kwargs)


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

    Returns:
        The decorator to be applied or the injected function if the
        argument :code:`func` was supplied.

    """

    def _inject(f):
        return wrapt.FunctionWrapper(
            wrapped=f,
            wrapper=Injector(
                container=container,
                blueprint=_generate_injection_blueprint(
                    func=f,
                    arg_map=arg_map,
                    use_names=use_names,
                    use_type_hints=use_type_hints
                )
            )
        )

    return func and _inject(func) or _inject


def _generate_args_kwargs(container: Optional[DependencyContainer],
                          bp: InjectionBlueprint,
                          args: Sequence,
                          kwargs: Dict,
                          skip_first=False
                          ) -> Tuple[Sequence, Dict]:
    """
    Generate the new arguments to be used by retrieving the missing
    dependencies based on the injection blueprint.

    If one argument has no default, is not set and is not mapped to a
    known dependency, :py:exc:`~..exceptions.DependencyNotFoundError` is
    raised.
    """
    if container is None:
        raise UndefinedContainerError()

    kwargs = kwargs.copy()

    for inj in islice(bp.injections, len(args) + (1 if skip_first else 0), None):
        if inj is not None and inj.arg_name not in kwargs:
            try:
                kwargs[inj.arg_name] = container[inj.dependency_id]
            except DependencyNotFoundError:
                if inj.required:
                    raise

    return args, kwargs


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
        Injection(arg_name=arg.name, required=not arg.has_default,
                  dependency_id=dependency_id)
        if dependency_id is not None else
        None
        for arg, dependency_id in zip(arg_spec.arguments, dependencies)
    ]))
