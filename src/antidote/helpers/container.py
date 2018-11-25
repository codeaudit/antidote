import weakref

from ..container import DependencyContainer
from ..providers import FactoryProvider, GetterProvider
from ..providers.tags import TagProvider
from .registration import provider


def new_container(providers=(FactoryProvider, GetterProvider, TagProvider)
                  ) -> DependencyContainer:
    container = DependencyContainer()
    container[DependencyContainer] = weakref.proxy(container)

    for p in providers:
        provider(p, container=container)

    return container
