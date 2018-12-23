from typing import Optional

from ..container import DependencyContainer


def get_global_container() -> DependencyContainer:
    import antidote
    return antidote.global_container


def set_global_container(container: DependencyContainer):
    import antidote
    antidote.global_container = container
