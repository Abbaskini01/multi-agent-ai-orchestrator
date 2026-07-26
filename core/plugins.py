"""
Neural Glass AI Orchestrator — Dynamic Plugin Ecosystem & Extension Engine
"""

import importlib.util
import inspect
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from core.logger import log_event


class BasePlugin:
    """Base interface for all Orchestrator plugins."""
    name: str = "BasePlugin"
    version: str = "1.0.0"
    description: str = "Base plugin interface"

    async def on_post_generation(self, files: Dict[str, str], state: dict) -> Dict[str, str]:
        """Hook triggered after code generation, before persistence."""
        return files

    async def on_pipeline_complete(self, state: dict) -> None:
        """Hook triggered after the pipeline successfully completes."""
        pass


class PluginRegistry:
    """Discovers, loads, and manages lifecycle hooks for external plugins."""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, BasePlugin] = {}

    def discover_and_load(self):
        """Scans the plugins directory and dynamically loads all valid plugins."""
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in self.plugins_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue

            module_name = f"plugins.{file_path.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                            plugin_instance = obj()
                            self.plugins[plugin_instance.name] = plugin_instance
                            log_event("plugin_loaded", plugin=plugin_instance.name, version=plugin_instance.version)
            except Exception as e:
                log_event("plugin_load_failed", file=file_path.name, error=str(e), level="error")

    async def run_post_generation_hooks(self, files: Dict[str, str], state: dict) -> Dict[str, str]:
        """Runs all registered on_post_generation hooks sequentially."""
        modified_files = files.copy()
        for plugin in self.plugins.values():
            try:
                modified_files = await plugin.on_post_generation(modified_files, state)
            except Exception as e:
                log_event("plugin_execution_error", plugin=plugin.name, hook="on_post_generation", error=str(e), level="error")
        return modified_files

    async def run_pipeline_complete_hooks(self, state: dict) -> None:
        """Runs all registered on_pipeline_complete hooks."""
        for plugin in self.plugins.values():
            try:
                await plugin.on_pipeline_complete(state)
            except Exception as e:
                log_event("plugin_execution_error", plugin=plugin.name, hook="on_pipeline_complete", error=str(e), level="error")

    def get_loaded_plugins(self) -> List[Dict[str, str]]:
        """Returns metadata for all loaded plugins."""
        return [
            {"name": p.name, "version": p.version, "description": p.description}
            for p in self.plugins.values()
        ]


# Global plugin registry singleton
plugin_registry = PluginRegistry()