def classFactory(iface):
    from .catastale_filter import CatastaleFilterPlugin
    return CatastaleFilterPlugin(iface)