# -*- coding: utf-8 -*-
"""The chain plugins manager object."""


class ChainPluginsManager(object):
    """Class that implements the chain plugins manager."""

    _plugin_classes = {}

    @classmethod
    def deregister_plugin(cls, plugin_class):
        """Deregisters a plugin class.

        The plugin classes are identified based on their lower case name.

        Args:
          plugin_class (type): the class object of the plugin.

        Raises:
          KeyError: if plugin class is not set for the corresponding name.
        """
        plugin_name = plugin_class.NAME.lower()
        if plugin_name not in cls._plugin_classes:
            raise KeyError(
                "Plugin class not set for name: {0:s}.".format(plugin_class.NAME)
            )

        del cls._plugin_classes[plugin_name]

    @classmethod
    def get_plugins(cls, analyzer_object):
        """Retrieves the chain plugins.

        Args:
            analyzer_object: an instance of Sketch object.

        Returns:
            list[type]: list of all chain plugin objects.
        """
        return [
            plugin_class(analyzer_object)
            for plugin_class in iter(cls._plugin_classes.values())
        ]

    @classmethod
    def register_plugin(cls, plugin_class):
        """Registers a plugin class.

        The plugin classes are identified based on their lower case name.

        Args:
            plugin_class (type): the class object of the plugin.

        Raises:
            KeyError: if plugin class is already set for the corresponding
            name.
        """
        plugin_name = plugin_class.NAME.lower()
        if plugin_name in cls._plugin_classes:
            raise KeyError(
                ("Plugin class already set for : {0:s}.").format(plugin_class.NAME)
            )

        cls._plugin_classes[plugin_name] = plugin_class

    @classmethod
    def register_plugins(cls, plugin_classes):
        """Registers plugin classes.

        The plugin classes are identified based on their lower case name.

        Args:
            plugin_classes (list[type]): a list of class objects of the
            plugins.

        Raises:
            KeyError: if plugin class is already set for the corresponding
            name.
        """
        for plugin_class in plugin_classes:
            cls.register_plugin(plugin_class)
