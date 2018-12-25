import inspect
from typing import Any, Callable, Iterable, Union, cast

from .._internal.global_container import get_global_container
from .._internal.helpers import prepare_callable, prepare_class
from ..core import DependencyContainer, DependencyProvider
from ..injection import ARG_MAP_TYPE, inject
from ..providers import FactoryProvider, ResourceProvider, Tag, TagProvider


def include():
    pass


def register(class_: type = None,
             *,
             singleton: bool = True,
             factory: Union[Callable, str] = None,
             auto_wire: Union[bool, Iterable[str]] = None,
             arg_map: ARG_MAP_TYPE = None,
             use_names: Union[bool, Iterable[str]] = None,
             use_type_hints: Union[bool, Iterable[str]] = None,
             tags: Iterable[Union[str, Tag]] = None,
             container: DependencyContainer = None
             ) -> Union[Callable, type]:
    """Register a dependency by its class.

    Args:
        class_: Class to register as a dependency. It will be instantiated
            only when requested.
        singleton: If True, the class will be instantiated only once,
            further will receive the same instance.
        factory: Callable to be used when building the class, this allows to
            re-use the same factory for subclasses for example. The dependency
            is given as first argument. If a string is specified, it is
            interpreted as the name of the method which has to be used to build
            the class. The dependency is given as first argument for static
            methods but not for class methods.
        auto_wire: Injects automatically the dependencies of the methods
            specified, or only of :code:`__init__()` if True.
        arg_map: Can be either a mapping of arguments name to their dependency,
            an iterable of dependencies or a function which returns the
            dependency given the arguments name. If an iterable is specified,
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
        tags: Iterable of tag to be applied. Those must be either strings
            (the tag name) or :py:class:`~.providers.tag.Tag`. All
            dependencies with a specific tag can then be retrieved with
            a :py:class:`~.providers.tag.Tagged`.
        container: :py:class:~.core.base.DependencyContainer` to which the
            dependency should be attached. Defaults to the global core if
            it is defined.

    Returns:
        The class or the class decorator.

    """
    container = container or get_global_container()

    def register_class(cls):
        nonlocal auto_wire, factory
        takes_dependency = True

        # If the factory is the class itself or if it's a classmethod, it is
        # not necessary to inject the dependency ID.
        if factory is None or (isinstance(factory, str)
                               and inspect.ismethod(getattr(cls, factory))):
            takes_dependency = False

        if auto_wire is None:
            if isinstance(factory, str):
                auto_wire = (factory,)
            elif factory is None:
                auto_wire = ('__init__',)
            else:
                auto_wire = False

        cls = prepare_class(cls,
                            auto_wire=auto_wire,
                            arg_map=arg_map,
                            use_names=use_names,
                            use_type_hints=use_type_hints,
                            container=container)

        if factory is None:
            injected_factory = cls
        elif isinstance(factory, str):
            injected_factory = getattr(cls, factory)
        elif callable(factory):
            injected_factory = inject(factory,
                                      arg_map=arg_map,
                                      use_names=use_names,
                                      use_type_hints=use_type_hints,
                                      container=container)
        else:
            raise ValueError("factory must be either a method name or a callable, "
                             "not {!r}".format(type(factory)))

        factory_provider = cast(FactoryProvider, container.providers[FactoryProvider])
        factory_provider.register(dependency=cls,
                                  factory=injected_factory,
                                  singleton=singleton,
                                  takes_dependency=takes_dependency)

        if tags is not None:
            tag_provider = cast(TagProvider, container.providers[TagProvider])
            tag_provider.register(cls, tags)

        return cls

    return class_ and register_class(class_) or register_class


def factory(func: Callable = None,
            *,
            dependency: Any = None,
            dependencies: Iterable[Any] = None,
            auto_wire: Union[bool, Iterable[str]] = True,
            singleton: bool = True,
            arg_map: ARG_MAP_TYPE = None,
            use_names: Union[bool, Iterable[str]] = None,
            use_type_hints: Union[bool, Iterable[str]] = None,
            tags: Iterable[Union[str, Tag]] = None,
            container: DependencyContainer = None
            ) -> Callable:
    """Register a dependency providers, a factory to build the dependency.

    Args:
        func: Callable which builds the dependency.
        dependency: Dependency built by the decorated factory. Overrides the
            return type hint. This is not compatible with the parameter
            :code:`dependencies`.
        dependencies: Dependencies built by the decorated factory. If used,
            the factory must accept the dependency as its first argument. This i
            s not compatible with the parameter :code:`dependency`.
        singleton: If True, `func` will only be called once. If not it is
            called at each injection.
        auto_wire: If :code:`func` is a function, its dependencies are
            injected if True. Should :code:`func` be a class with
            :py:func:`__call__`, dependencies of :code:`__init__()` and
            :code:`__call__()` will be injected if True. One may also
            provide an iterable of method names requiring dependency
            injection.
        arg_map: Can be either a mapping of arguments name to their dependency,
            an iterable of dependencies or a function which returns the
            dependency given the arguments name. If an iterable is specified,
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
        tags: Iterable of tag to be applied. Those must be either strings
            (the tag name) or :py:class:`~.providers.tag.Tag`. All
            dependencies with a specific tag can then be retrieved with
            a :py:class:`~.providers.tag.Tagged`.
        container: :py:class:~.core.base.DependencyContainer` to which the
            dependency should be attached. Defaults to the global core if
            it is defined.

    Returns:
        object: The dependency_provider

    """
    container = container or get_global_container()

    if dependencies is not None and dependency is not None:
        raise ValueError("Cannot define both dependencies and dependency")

    def register_factory(obj):
        nonlocal dependency
        obj, factory_, return_type_hint = prepare_callable(
            obj,
            auto_wire=auto_wire,
            arg_map=arg_map,
            use_names=use_names,
            use_type_hints=use_type_hints,
            container=container
        )

        takes_dependency = False
        if dependencies is not None:
            _dependencies = dependencies
            takes_dependency = True
        elif dependency is not None:
            _dependencies = [dependency]
        else:
            _dependencies = [return_type_hint]

        _dependencies = [did for did in _dependencies if did is not None]

        if not _dependencies:
            raise ValueError("No dependency defined.")

        for _dependency in _dependencies:
            factory_provider = cast(FactoryProvider,
                                    container.providers[FactoryProvider])
            factory_provider.register(factory=factory_,
                                      singleton=singleton,
                                      dependency=_dependency,
                                      takes_dependency=takes_dependency)

        if tags is not None:
            tag_provider = cast(TagProvider, container.providers[TagProvider])
            for _dependency in _dependencies:
                tag_provider.register(dependency=_dependency,
                                      tags=tags)

        return obj

    return func and register_factory(func) or register_factory


def provider(class_: type = None,
             *,
             auto_wire: Union[bool, Iterable[str]] = True,
             arg_map: ARG_MAP_TYPE = None,
             use_names: Union[bool, Iterable[str]] = None,
             use_type_hints: Union[bool, Iterable[str]] = None,
             container: DependencyContainer = None):
    """Register a providers by its class.

    Args:
        class_: class to register as a provider. The class must have a
            :code:`__antidote_provide()` method accepting as first argument
            the dependency. Variable keyword and positional arguments must be
            accepted as they may be provided.
        auto_wire: If True, the dependencies of :code:`__init__()` are
            injected. An iterable of method names which require dependency
            injection may also be specified.
        arg_map: Can be either a mapping of arguments name to their dependency,
            an iterable of dependencies or a function which returns the
            dependency given the arguments name. If an iterable is specified,
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
        container: :py:class:~.core.base.DependencyContainer` to which the
            dependency should be attached. Defaults to the global core if
            it is defined.

    Returns:
        the providers's class or the class decorator.
    """
    container = container or get_global_container()

    def register_provider(cls):
        if not issubclass(cls, DependencyProvider):
            raise ValueError("A provider must be subclass of Provider.")

        cls = prepare_class(cls,
                            auto_wire=auto_wire,
                            arg_map=arg_map,
                            use_names=use_names,
                            use_type_hints=use_type_hints,
                            container=container)

        container.register_provider(cls())

        return cls

    return class_ and register_provider(class_) or register_provider


def resource(func: Callable[[str], Any] = None,
             *,
             singleton: bool = True,
             namespace: str = None,
             omit_namespace: bool = None,
             priority: float = 0,
             auto_wire: Union[bool, Iterable[str]] = True,
             arg_map: ARG_MAP_TYPE = None,
             use_names: Union[bool, Iterable[str]] = None,
             use_type_hints: Union[bool, Iterable[str]] = None,
             container: DependencyContainer = None
             ) -> Callable:
    """
    Register a mapping of parameters and its associated parser.

    Args:
        func: Function used to retrieve a requested dependency which will
            be given as an argument. If the dependency cannot be provided,
            it should raise a :py:exc:`LookupError`.
        singleton: If True, `func` will only be called once. If not it is
            called at each injection.
        namespace: Used to identity which getter should be used with a
            dependency. It should only contain characters in
            :code:`[a-zA-Z0-9_]`.
        priority: Used to determine which getter should be called first when
            they share the same namespace. Highest priority wins. Defaults to
            0.
        omit_namespace: Whether or not the namespace should be kept when
            passing the dependency to the :code:`resource_getter`. Defaults
            to True.
        auto_wire: If True, the dependencies of :code:`__init__()` are
            injected. An iterable of method names which require dependency
            injection may also be specified.
        arg_map: Can be either a mapping of arguments name to their dependency,
            an iterable of dependencies or a function which returns the
            dependency given the arguments name. If an iterable is specified,
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
        container: :py:class:~.core.base.DependencyContainer` to which the
            dependency should be attached. Defaults to the global core if
            it is defined.

    Returns:
        getter callable or decorator.
    """
    container = container or get_global_container()

    def register_getter(obj):
        nonlocal namespace, omit_namespace
        omit_namespace = omit_namespace if omit_namespace is not None else True

        if namespace is None:
            namespace = obj.__name__

        obj, getter_, _ = prepare_callable(obj,
                                           auto_wire=auto_wire,
                                           arg_map=arg_map,
                                           use_names=use_names,
                                           use_type_hints=use_type_hints,
                                           container=container)

        resource_provider = cast(ResourceProvider,
                                 container.providers[ResourceProvider])
        resource_provider.register(resource_getter=getter_,
                                   namespace=namespace,
                                   omit_namespace=omit_namespace,
                                   priority=priority,
                                   singleton=singleton)

        return obj

    return func and register_getter(func) or register_getter
