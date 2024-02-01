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
from typing import Any, Optional, Type, TypeVar

from pydantic import BaseModel

from aineko.utils.imports import import_from_string

T = TypeVar("T", bound="AbstractDataset")


class DatasetError(Exception):
    """``DatasetError`` raised by ``AbstractDataset`` implementations
    in case of failure of input/output methods.

    ``AbstractDataset`` implementations should provide instructive
    information in case of failure.
    """

    pass


class AbstractDatasetConfig(BaseModel):
    """Dataset configuration model."""

    type: str
    target: str
    params: dict[str, Any] = {}


class DatasetCreateStatus:
    """Object representing staus of dataset creation."""

    def __init__(
        self,
        dataset_name: str,
        kafka_topic_to_future: dict[str, Any] | None = None,
        status_list: list[Any] | None = None,
    ):
        self.dataset_name = dataset_name
        self.kafka_topic_to_future = kafka_topic_to_future
        self.status_list = status_list

    def done(self) -> bool:
        """Return status of dataset creation."""
        if not any([self.kafka_topic_to_future, self.status_list]):
            return True
        if self.kafka_topic_to_future:
            return all(
                [
                    future.done()
                    for future in self.kafka_topic_to_future.values()
                ]
            )
        if self.status_list:
            return all(status.done() for status in self.status_list)


class AbstractDataset(abc.ABC):
    @classmethod
    def from_config(cls: Type[T], name: str, config: dict[str, Any]) -> T:
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

    def read(self,*args,**kwargs) -> Any:
        """Read the dataset."""
        try:
            return self._read(*args,**kwargs)
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to read dataset {self.name}."
            raise DatasetError(message) from e

    def write(self,*args,**kwargs) -> None:
        """Write the dataset."""
        try:
            return self._write(*args,**kwargs)
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to write dataset {self.name}."
            raise DatasetError(message) from e

    def create(self,*args,**kwargs) -> None:
        """Create the dataset."""
        try:
            return self._create(*args,**kwargs)
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

    @abc.abstractmethod
    def _read(self) -> Any:
        """Read the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def _write(self) -> None:
        """Write the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def _create(self) -> None:
        """Create the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def _delete(self) -> None:
        """Delete the dataset."""
        raise NotImplementedError

    @abc.abstractmethod
    def _describe(self) -> str:
        """Describe the dataset metadata."""
        return f"Dataset name: {self.name}"
