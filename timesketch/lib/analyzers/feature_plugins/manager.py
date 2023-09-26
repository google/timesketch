"""The feature extraction plugins manager object."""

from typing import List


class FeatureExtractionPluginManager(object):
    """ "A class that implements the plugins manager."""

    _plugin_classes = {}

    @classmethod
    def register_plugin(cls, plugin_class) -> None:
        """Registers a plugin class.

        Args:
            plugin_class (type): A class object of a plugin.

        Raises:
            KeyError: If the `plugin_class` is already registered.
        """

        plugin_name = plugin_class.NAME.lower()
        if plugin_name in cls._plugin_classes:
            raise KeyError(f"Plugin class {plugin_class.NAME} is already registered.")

        cls._plugin_classes[plugin_name] = plugin_class

    @classmethod
    def register_plugins(cls, plugin_classes) -> None:
        """Registers multiple plugin classes.

        Args:
            plugin_classes (List[type]): A list of plugin class objects.

        Raises:
            KeyError: If plugin classes are already registered.
        """

        for plugin_class in plugin_classes:
            cls.register_plugin(plugin_class=plugin_class)

    @classmethod
    def deregister_plugin(cls, plugin_class) -> None:
        """Deregisters a plugin class.

        Args:
            plugin_class (type): A plugin class to be deregistered.

        Raises:
            KeyError: If the plugin class is not registered.
        """

        plugin_name = plugin_class.NAME.lower()
        if plugin_name not in cls._plugin_classes:
            raise KeyError(f"Plugin class {plugin_class.NAME} is not registered.")

        del cls._plugin_classes[plugin_name]

    @classmethod
    def get_plugins(cls, analyzer_object) -> List:
        """Retrieves plugins classes.

        Args:
            analayzer_object (FeatureExtractionSketchPlugin): An instance of
                FeatureSketchPlugin.

        Returns:
            List[type]: A list of plugin class.
        """

        return [
            plugin_class(analyzer_object)
            for plugin_class in iter(cls._plugin_classes.values())
        ]
