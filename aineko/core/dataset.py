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
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel

from aineko.utils.imports import import_from_string

A = TypeVar("A", bound="AbstractDataset")
T = TypeVar("T")


class DatasetError(Exception):
    """Generic Dataset Error.

    ``DatasetError`` raised by ``AbstractDataset`` implementations
    in case of failure of methods.

    ``AbstractDataset`` implementations should provide instructive
    information in case of failure.
    """

    pass


class AbstractDatasetConfig(BaseModel):
    """Dataset configuration model."""

    type: str
    location: Optional[str]
    params: Optional[Dict[str, Any]] = {}


class DatasetCreateStatus:
    """Object representing staus of dataset creation.

    Represents creation status of dataset (such as a kafka topic)
    or its connections (such as producers and consumers linked
    to the topic).

    Can be used to ensure all datasets have been created.

    Attributes:
        dataset_name: Name of the dataset.
        kafka_topic_to_future: Dictionary of kafka topics to futures.
        status_list: List of status of dataset creation.

    Args:
        dataset_name: Name of the dataset.
        kafka_topic_to_future: Dictionary of kafka topics to futures.
        status_list: List of status of dataset creation.
    """

    def __init__(
        self,
        dataset_name: str,
        kafka_topic_to_future: Optional[Dict[str, Any]] = None,
        status_list: Optional[List[Any]] = None,
    ):
        """Creation status of dataset or its components."""
        self.dataset_name = dataset_name
        self.kafka_topic_to_future = kafka_topic_to_future
        self.status_list = status_list

    def done(self) -> bool:
        """Return status of dataset creation.

        For kafka topics, the status is represented by a dictionary
        of kafka topics to futures. For kafka producers and consumers,
        the status is represented by a list of status objects.

        Returns:
            True if all futures are done, otherwise False.
        """
        if not any([self.kafka_topic_to_future, self.status_list]):
            return True
        if self.kafka_topic_to_future:
            return all(
                future.done() for future in self.kafka_topic_to_future.values()
            )
        if self.status_list:
            return all(status.done() for status in self.status_list)
        return False


class AbstractDataset(abc.ABC, Generic[T]):
    """Base class for defining new synchronous Aineko datasets.

    Subclass implementations can be instantiated using
    the `from_config` method.

    When defining a new dataset, the following methods must be implemented:

    ```
    - `_read`
    - `_write`
    - `_create`
    - `_delete`
    - `_initialize`
    - `_exists`
    ```

    Example:
    ```python
    class MyDataset(AbstractDataset):
        def _read(self, **kwargs) -> Any:
            pass

        def _write(self, **kwargs) -> Any:
            pass

        def _create(self, **kwargs) -> Any:
            pass

        def _delete(self, **kwargs) -> Any:
            pass

        def _initialize(self, **kwargs) -> Any:
            pass

        def _exists(self, **kwargs) -> bool:
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
        dataset_config = AbstractDatasetConfig(**dict(config))

        class_obj = import_from_string(dataset_config.type, kind="class")
        class_instance = class_obj(name, dict(dataset_config))
        class_instance.name = name
        return class_instance

    @abc.abstractmethod
    def read(self, *args: T, **kwargs: T) -> Any:
        """Subclass implementation to read the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, *args: T, **kwargs: T) -> Any:
        """Subclass implementation to write the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, *args: T, **kwargs: T) -> Any:
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
        """Subclass implementation to check if the dataset exists."""
        raise NotImplementedError
