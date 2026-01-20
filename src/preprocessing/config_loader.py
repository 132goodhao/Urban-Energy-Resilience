# -*- coding: utf-8 -*-
"""
Configuration loader module.
配置加载工具模块

This module provides utilities for loading and managing project configuration
from YAML files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    raise ImportError(
        "PyYAML is required. Install it with: pip install PyYAML"
    )


class ConfigLoader:
    """
    Configuration loader class for managing project settings.

    Loads configuration from a YAML file and provides convenient access
    to nested configuration values.

    Attributes:
        config (Dict[str, Any]): The loaded configuration dictionary.
        config_path (Path): Path to the configuration file.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ConfigLoader.

        Args:
            config_path: Path to the configuration file. If None, uses the
                        default path 'config/config.yaml' relative to project root.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            yaml.YAMLError: If the configuration file is not valid YAML.
        """
        if config_path is None:
            # Default to config/config.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self._load_config()

    def _load_config(self) -> None:
        """
        Load the configuration from the YAML file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            yaml.YAMLError: If the configuration file is not valid YAML.
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key_path: Dot-separated path to the configuration value.
                     Example: 'paths.data_dir' or 'study.start_year'
            default: Default value to return if the key is not found.

        Returns:
            The configuration value, or default if not found.

        Example:
            >>> loader = ConfigLoader()
            >>> data_dir = loader.get('paths.data_dir')
            >>> start_year = loader.get('study.start_year', 2001)
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_paths(self) -> Dict[str, str]:
        """
        Get all path configurations.

        Returns:
            Dictionary of path configurations.
        """
        return self.config.get('paths', {})

    def get_data_files(self) -> Dict[str, str]:
        """
        Get all data file configurations.

        Returns:
            Dictionary of data file paths.
        """
        return self.config.get('data_files', {})

    def get_study_params(self) -> Dict[str, Any]:
        """
        Get all study parameters.

        Returns:
            Dictionary of study parameters.
        """
        return self.config.get('study', {})

    def get_attack_recovery_params(self) -> Dict[str, Any]:
        """
        Get attack-recovery simulation parameters.

        Returns:
            Dictionary of attack-recovery parameters.
        """
        return self.config.get('attack_recovery', {})

    def get_resilience_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Get resilience indicator weights for all levels.

        Returns:
            Dictionary of weights for each resilience level.
        """
        return self.config.get('resilience_weights', {})

    def get_computation_config(self) -> Dict[str, Any]:
        """
        Get computation configuration.

        Returns:
            Dictionary of computation settings.
        """
        return self.config.get('computation', {})

    def get_visualization_config(self) -> Dict[str, Any]:
        """
        Get visualization configuration.

        Returns:
            Dictionary of visualization settings.
        """
        return self.config.get('visualization', {})

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.

        Returns:
            Dictionary of logging settings.
        """
        return self.config.get('logging', {})

    def resolve_path(self, relative_path: str) -> Path:
        """
        Resolve a relative path to an absolute path based on project root.

        Args:
            relative_path: Path relative to project root.

        Returns:
            Absolute Path object.
        """
        project_root = self.config_path.parent.parent
        return project_root / relative_path

    def get_full_path(self, file_key: str) -> Optional[Path]:
        """
        Get the full path for a configured data file.

        Args:
            file_key: Key in the 'data_files' section of config.

        Returns:
            Absolute Path object, or None if the key is not found.
        """
        relative_path = self.get(f'data_files.{file_key}')
        if relative_path is None:
            return None
        return self.resolve_path(relative_path)


# Global config loader instance (lazy-loaded)
_config_instance: Optional[ConfigLoader] = None


def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Get or create the global config loader instance.

    Args:
        config_path: Optional path to config file. Only used on first call.

    Returns:
        The ConfigLoader instance.

    Example:
        >>> config = get_config()
        >>> data_dir = config.get('paths.data_dir')
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigLoader(config_path)
    return _config_instance
