# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Essential classes and objects for the dataset layer.

Example dataset configuration:

    ```yaml
    datasets:
        my_dataset:
            type: aineko.datasets.kafka.KafkaDataset
            location: localhost:9092
            params:
                param_1: bar
    ```
"""
import abc
from concurrent.futures import Future
from typing import Any, Dict, Generic, Optional, TypeVar

from aineko.models.dataset_config_schema import DatasetConfig
from aineko.utils.imports import import_from_string

T = TypeVar("T")


class DatasetError(Exception):
    """Generic Dataset Error.

    ``DatasetError`` raised by ``AbstractDataset`` implementations
    in case of failure of methods.

    ``AbstractDataset`` implementations should provide instructive
    information in case of failure.
    """

    pass


class DatasetCreationStatus:
    """Status of dataset creation.

    Attributes:
        dataset_name: Name of the dataset.
        _future: Future representing the creation status of the dataset.

    Usage:
        ```python
        dataset = MyDataset("my_dataset")
        creation_status = dataset.create()
        if creation_status.done():
            print(f"Dataset {creation_status.dataset_name} has been created.")
        else:
            print(f"Dataset {creation_status.dataset_name} is being created.")
        ```
    """

    def __init__(self, dataset_name: str, future: Optional[Future] = None):
        """Initialize the dataset creation status."""
        self.dataset_name = dataset_name
        self._future = future

    def done(self) -> bool:
        """Check if the dataset has been created.

        Returns:
            True if the dataset has been created, otherwise False.
        """
        if self._future:
            return self._future.done()
        return True


class AbstractDataset(abc.ABC, Generic[T]):
    """Base class for defining new synchronous Aineko datasets.

    Subclass implementations can be instantiated using
    the `from_config` method.

    When defining a new dataset, the following methods must be implemented:

    ```
    - `read`
    - `write`
    - `create`
    - `delete`
    - `initialize`
    - `exists`
    ```

    Example:
    ```python
    class MyDataset(AbstractDataset):
        def read(self, **kwargs) -> Any:
            pass

        def write(self, **kwargs) -> Any:
            pass

        def create(self, **kwargs) -> DatasetCreationStatus:
            pass

        def delete(self, **kwargs) -> Any:
            pass

        def initialize(self, **kwargs) -> Any:
            pass

        def exists(self, **kwargs) -> bool:
            pass
    ```

    If `MyDataset` was defined in the file
    `./aineko/datasets/mydataset.py`, a new dataset
    can be created using the `from_config` method:

    Example:
    ```python

    dataset = AbstractDataset.from_config(
        name="my_dataset_instance",
        config={
            "type": "aineko.datasets.mydataset.MyDataset",
            "location": "foo",
            "params": {
                "param_1": "bar"
            }
        }
    )
    ```
    """

    name: str

    def __str__(self) -> str:
        """Return the string representation of the dataset."""
        return f"{self.__class__.__name__}({self.name})"

    @classmethod
    def from_config(
        cls, name: str, config: Dict[str, Any]
    ) -> "AbstractDataset":
        """Create a dataset from a configuration dictionary.

        Args:
            name: The name of the dataset.
            config: The configuration dictionary.

        Returns:
            Instance of an `AbstractDataset` subclass.
        """
        dataset_config = DatasetConfig(**dict(config))

        class_obj = import_from_string(dataset_config.type, kind="class")
        class_instance = class_obj(name, dict(dataset_config))
        class_instance.name = name
        return class_instance

    @abc.abstractmethod
    def read(self, *args: T, **kwargs: T) -> Any:
        """Subclass implementation to read an entry from the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, *args: T, **kwargs: T) -> Any:
        """Subclass implementation to write an entry to the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, *args: T, **kwargs: T) -> DatasetCreationStatus:
        """Subclass implementation to create the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, *args: T, **kwargs: T) -> Any:
        """Subclass implementation to delete the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def initialize(self, *args: T, **kwargs: T) -> Any:
        """Subclass implementation to initialize the dataset query layer."""
        raise NotImplementedError

    @abc.abstractmethod
    def exists(self, *args: T, **kwargs: T) -> bool:
        """Subclass implementation to check if the dataset exists.

        This method should return True if the dataset exists, otherwise False.
        """
        raise NotImplementedError
