import contextlib
import weakref
from typing import (Any, Callable, Dict, Iterable, Mapping, Sequence, Type, Union,
                    get_type_hints)

from ._internal.argspec import get_arguments_specification
from .container import DependencyContainer
from .container.proxy import ProxyContainer
from .helpers import factory, getter, new_container, provider, register
from .injection import inject, wire
from .providers import Provider
from .providers.tags import Tag


class DependencyManager:
    """Provides utility functions/decorators to manage dependencies.

    Except for :py:meth:`attrib()` all functions can either be used as
    decorators or functions to directly modify an object.

    Custom instances or classes can be used as :py:attr:`container` and
    :py:attr:`injector`.

    """

    def __init__(self,
                 auto_wire: bool = None,
                 use_names: bool = None,
                 arg_map: Mapping[str, Any] = None,
                 container: DependencyContainer = None,
                 injector=None
                 ) -> None:
        """Initialize the DependencyManager.

        Args:
            auto_wire: Default value for :code:`auto_wire` argument.
            use_names: Default value for :code:`use_names` argument.
            container: Container to use if specified.
            injector: Injector to use if specified.

        """
        self.auto_wire = auto_wire if auto_wire is not None else True
        self.use_names = use_names if use_names is not None else False
        self.arg_map = dict()  # type: Dict[str, Any]
        self.arg_map.update(arg_map or dict())

        self.container = container or new_container()

    @contextlib.contextmanager
    def context(self,
                dependencies: Mapping = None,
                include: Iterable = None,
                exclude: Iterable = None,
                missing: Iterable = None
                ):
        """
        Creates a context within one can control which of the defined
        dependencies available or not. Any changes will be discarded at the
        end.

        >>> from antidote import antidote, DependencyContainer
        >>> with antidote.context(include=[]):
        ...     # Your code isolated from every other dependencies
        ...     antidote.container[DependencyContainer]
        <... DependencyContainer ...>

        The :py:class:`~antidote.DependencyInjector` and the
        :py:class:`~antidote.DependencyContainer` will still be accessible.

        Args:
            dependencies: Dependencies instances used to override existing ones
                in the new context.
            include: Iterable of dependencies to include. If None
                everything is accessible.
            exclude: Iterable of dependencies to exclude.
            missing: Iterable of dependencies which should raise a
                :py:exc:`~.exceptions.DependencyNotFoundError` even if a
                provider could instantiate them.

        """
        container = ProxyContainer(container=self.container,
                                   dependencies=dependencies,
                                   include=include,
                                   exclude=exclude,
                                   missing=missing)
        container[DependencyContainer] = weakref.proxy(container)

        original_container, self.container = self.container, container
        try:
            yield
        finally:
            self.container = original_container
