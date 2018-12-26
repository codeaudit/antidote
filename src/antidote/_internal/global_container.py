from ..core import DependencyContainer


def get_global_container() -> DependencyContainer:
    import antidote
    return antidote.world


def set_global_container(container: DependencyContainer):
    import antidote
    antidote.world = container
