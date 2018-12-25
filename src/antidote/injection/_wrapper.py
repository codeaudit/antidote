from typing import Callable, Sequence

from .._internal.utils import SlotsReprMixin
from ..core import DependencyContainer
from ..exceptions import DependencyNotFoundError


class Injection(SlotsReprMixin):
    """
    Maps an argument name to its dependency and if the injection is required,
    which is equivalent to no default argument.
    """
    __slots__ = ('arg_name', 'required', 'dependency')

    def __init__(self, arg_name: str, required: bool, dependency):
        self.arg_name = arg_name
        self.required = required
        self.dependency = dependency


class InjectionBlueprint(SlotsReprMixin):
    """
    Stores all the injections for a function.
    """
    __slots__ = ('injections',)

    def __init__(self, injections: Sequence[Injection]):
        self.injections = injections


class InjectedCallableWrapper:
    """
    Wrapper which injects all the dependencies not supplied in the passed
    arguments. An InjectionBlueprint is used to store the mapping of the
    arguments to their dependency if any and if the injection is required.
    """

    def __init__(self,
                 container: DependencyContainer,
                 blueprint: InjectionBlueprint,
                 wrapped: Callable,
                 skip_self: bool = False):
        self.__wrapped__ = wrapped
        self.__container = container
        self.__blueprint = blueprint
        self.__injection_offset = 1 if skip_self else 0

    def __call__(self, *args, **kwargs):
        kwargs = _inject_kwargs(
            self.__container,
            self.__blueprint,
            self.__injection_offset + len(args),
            kwargs
        )
        return self.__wrapped__(*args, **kwargs)

    def __get__(self, instance, owner):
        skip_self = instance is not None
        func = self.__wrapped__.__get__(instance, owner)
        return InjectedBoundCallableWrapper(self.__container, self.__blueprint,
                                            func, skip_self=skip_self)


class InjectedBoundCallableWrapper(InjectedCallableWrapper):
    """
    Wrapper necessary to correctly handle methods.
    """

    def __get__(self, instance, owner):
        return self


def _inject_kwargs(container: DependencyContainer,
                   blueprint: InjectionBlueprint,
                   offset: int,
                   kwargs: dict) -> dict:
    """
    Does the actual injection of the dependencies. Used by InjectedCallableWrapper.
    """
    dirty_kwargs = False
    for injection in blueprint.injections[offset:]:
        if injection.dependency is not None and injection.arg_name not in kwargs:
            instance = container.provide(injection.dependency)
            if instance is not container.SENTINEL:
                if not dirty_kwargs:
                    kwargs = kwargs.copy()
                    dirty_kwargs = True
                kwargs[injection.arg_name] = instance
            elif injection.required:
                raise DependencyNotFoundError(injection.dependency)

    return kwargs
