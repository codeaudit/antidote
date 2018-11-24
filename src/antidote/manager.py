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

    def __repr__(self):
        return (
            "{}(auto_wire={!r}, mapping={!r}, use_names={!r}, "
            "container={!r})"
        ).format(type(self).__name__, self.auto_wire, self.arg_map,
                 self.use_names, self.container)

    @property
    def providers(self) -> Dict[Type[Provider], Provider]:
        return self.container.providers

    def inject(self,
               func: Callable = None,
               arg_map: Union[Mapping, Sequence] = None,
               use_names: Union[bool, Iterable[str]] = None,
               use_type_hints: Union[bool, Iterable[str]] = None,
               bind: bool = False
               ) -> Callable:
        if use_names is None:
            use_names = self.use_names

        def _inject(f):
            _mapping = self.arg_map.copy()
            if isinstance(arg_map, Mapping):
                _mapping.update(arg_map)
            elif isinstance(arg_map, Sequence):
                arg_spec = get_arguments_specification(f)
                for arg, dependency_id in zip(arg_spec.arguments, arg_map):
                    _mapping[arg.name] = dependency_id

            return inject(f, _mapping, use_names, use_type_hints, self.container)

        return func and _inject(func) or _inject

    def register(self,
                 class_: type = None,
                 singleton: bool = True,
                 auto_wire: Union[bool, Iterable[str]] = None,
                 arg_map: Union[Mapping, Sequence] = None,
                 use_names: Union[bool, Iterable[str]] = None,
                 use_type_hints: Union[bool, Iterable[str]] = None,
                 tags: Iterable[Union[str, Tag]] = None
                 ) -> Union[Callable, type]:
        if auto_wire is None:
            auto_wire = self.auto_wire

        def register_class(cls):
            return register(cls, singleton, auto_wire, arg_map, use_names,
                            use_type_hints,
                            tags, self.container)

        return class_ and register_class(class_) or register_class

    def factory(self,
                func: Callable = None,
                dependency_id: Any = None,
                auto_wire: Union[bool, Iterable[str]] = None,
                singleton: bool = True,
                arg_map: Union[Mapping, Sequence] = None,
                use_names: Union[bool, Iterable[str]] = None,
                use_type_hints: Union[bool, Iterable[str]] = None,
                build_subclasses: bool = False,
                tags: Iterable[Union[str, Tag]] = None
                ) -> Callable:
        if auto_wire is None:
            auto_wire = self.auto_wire

        def register_factory(obj):
            return factory(obj, dependency_id, auto_wire, singleton, arg_map, use_names,
                           use_type_hints, build_subclasses, tags, self.container)

        return func and register_factory(func) or register_factory

    def wire(self,
             class_: type = None,
             methods: Iterable[str] = None,
             arg_map: Union[Mapping, Sequence] = None,
             use_names: Union[bool, Iterable[str]] = None,
             use_type_hints: Union[bool, Iterable[str]] = None,
             ) -> Union[Callable, type]:

        def wire_methods(cls):
            return wire(cls, methods, arg_map, use_names, use_type_hints,
                        self.container)

        return class_ and wire_methods(class_) or wire_methods

    def attrib(self,
               dependency_id: Any = None,
               use_name: bool = None,
               **attr_kwargs):
        """Injects a dependency with attributes defined with attrs package.

        Args:
            dependency_id: Id of the dependency to inject. Defaults to the
                annotation.
            use_name: If True, use the attribute name as the dependency id
                overriding any annotations.
            **attr_kwargs: Keyword arguments passed on to attr.ib()

        Returns:
            object: attr.Attribute with a attr.Factory.

        """
        try:
            import attr
        except ImportError:
            raise RuntimeError("attrs package must be installed.")

        if use_name is None:
            use_name = self.use_names

        def factory(instance):
            nonlocal dependency_id

            if dependency_id is None:
                cls = instance.__class__
                type_hints = get_type_hints(cls) or {}

                for attribute in attr.fields(cls):
                    # Dirty way to find the attrib annotation.
                    # Maybe attr will eventually provide the annotation ?
                    if isinstance(attribute.default, attr.Factory) \
                            and attribute.default.factory is factory:
                        try:
                            dependency_id = type_hints[attribute.name]
                        except KeyError:
                            if use_name:
                                dependency_id = attribute.name
                                break
                        else:
                            break
                else:
                    raise ValueError(
                        "No dependency could be detected. Please specify "
                        "the parameter `dependency_id` or `use_name=True`."
                        "Annotations may also be used."
                    )

            return self.container[dependency_id]

        return attr.ib(default=attr.Factory(factory, takes_self=True),
                       **attr_kwargs)

    def provider(self,
                 class_: type = None,
                 auto_wire: Union[bool, Iterable[str]] = None,
                 arg_map: Union[Mapping, Sequence] = None,
                 use_names: Union[bool, Iterable[str]] = None,
                 use_type_hints: Union[bool, Iterable[str]] = None,
                 ) -> Union[Callable, type]:
        if auto_wire is None:
            auto_wire = self.auto_wire

        def register_provider(cls):
            return provider(cls, auto_wire, arg_map, use_names, use_type_hints,
                            self.container)

        return class_ and register_provider(class_) or register_provider

    def getter(self,
               func: Callable[[str], Any] = None,
               namespace: str = None,
               omit_namespace: bool = None,
               auto_wire: Union[bool, Iterable[str]] = None,
               arg_map: Union[Mapping, Sequence] = None,
               use_names: Union[bool, Iterable[str]] = None,
               use_type_hints: Union[bool, Iterable[str]] = None,
               ) -> Callable:
        def register_getter(obj):
            return getter(obj, namespace, omit_namespace, auto_wire, arg_map,
                          use_names, use_type_hints, self.container)

        return func and register_getter(func) or register_getter

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
