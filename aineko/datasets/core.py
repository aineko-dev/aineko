# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
"""Essential classes and objects for the dataset layer.

Example dataset configuration:

    ```yaml
    datasets:
        my_dataset:
            type: aineko.datasets.MemoryDataset
            target: foo
            params:
                param_1: bar
    ```
"""
import abc
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from aineko.utils.imports import import_from_string

T = TypeVar("T", bound="AbstractDataset")


class DatasetError(Exception):
    """Generic Dataset Error.

    ``DatasetError`` raised by ``AbstractDataset`` implementations
    in case of failure of input/output methods.

    ``AbstractDataset`` implementations should provide instructive
    information in case of failure.
    """

    pass


class AbstractDatasetConfig(BaseModel):
    """Dataset configuration model."""

    type: str
    target: str
    params: Dict[str, Any] = {}


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


class AbstractDataset(abc.ABC):
    """Base class for defining new Aineko datasets.

    Subclass implementations can be instantiated using
    the `from_config` method.

    When defining a new dataset, the following methods must be implemented:
    - `_read`
    - `_write`
    - `_create`
    - `_delete`
    - `_initialize`
    - `_describe`

    Example:
    ```python
    class MyDataset(AbstractDataset):
        def _read(self, *args, **kwargs) -> Any:
            pass

        def _write(self, *args, **kwargs) -> None:
            pass

        def _create(self, *args, **kwargs) -> None:
            pass

        def _delete(self, *args, **kwargs) -> None:
            pass

        def _initialize(self, *args, **kwargs) -> None:
            pass

        def _describe(self, *args, **kwargs) -> str:
            pass
    ```

    If `MyDataset` was defined in the file
    `./aineko/datasets/mydataset.py`, a new dataset
    can be created using the `from_config` method:

        ```python
        dataset = AbstractDataset.from_config(
            name="my_dataset_instance",
            config={
                "type": "aineko.datasets.mydataset.MyDataset",
                "target": "foo",
                "params": {
                    "param_1": "bar"
                }
            }
        )
        ```
    """

    @classmethod
    def from_config(cls: Type[T], name: str, config: Dict[str, Any]) -> T:
        """Create a dataset from a configuration dictionary.

        Args:
            name: The name of the dataset.
            config: The configuration dictionary.

        Returns:
            Instance of an `AbstractDataset` subclass.
        """
        dataset_config = AbstractDatasetConfig(**config)

        class_obj = import_from_string(dataset_config.type, kind="class")

        return class_obj(name, dataset_config.params)

    def read(self, *args, **kwargs) -> Any:
        """Read the dataset."""
        try:
            return self._read(*args, **kwargs)
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to read dataset {self.name}."
            raise DatasetError(message) from e

    def write(self, *args, **kwargs) -> None:
        """Write the dataset."""
        try:
            return self._write(*args, **kwargs)
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to write dataset {self.name}."
            raise DatasetError(message) from e

    def create(self, *args, **kwargs) -> None:
        """Create the dataset."""
        try:
            return self._create(*args, **kwargs)
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to create dataset {self.name}."
            raise DatasetError(message) from e

    def delete(self) -> None:
        """Delete the dataset."""
        try:
            return self._delete()
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to delete dataset {self.name}."
            raise DatasetError(message) from e

    def initialize(self, *args, **kwargs) -> None:
        """Initialize the dataset query layer."""
        try:
            return self._initialize(*args, **kwargs)
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to initialize dataset {self.name}."
            raise DatasetError(message) from e

    @abc.abstractmethod
    def _read(self, *args, **kwargs) -> Any:
        """Read the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def _write(self, *args, **kwargs) -> None:
        """Write the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def _create(self, *args, **kwargs) -> None:
        """Create the dataset storage layer."""
        raise NotImplementedError

    @abc.abstractmethod
    def _delete(self, *args, **kwargs) -> None:
        """Delete the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def _initialize(self, *args, **kwargs) -> None:
        """Initialize the dataset query layer."""
        raise NotImplementedError

    @abc.abstractmethod
    def _describe(self, *args, **kwargs) -> str:
        """Describe the dataset metadata."""
        return f"Dataset name: {self.name}"
