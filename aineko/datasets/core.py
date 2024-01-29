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

from typing import Any, Optional

from pydantic import BaseModel

from aineko.utils.imports import import_from_string


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

    def __init__(self, dataset_name: str, kafka_topic_to_future: dict[str, Any] | None = None):
        self.dataset_name = dataset_name
        self.kafka_topic_to_future = kafka_topic_to_future

    def done(self) -> bool:
        """Return status of dataset creation."""
        if self.kafka_topic_to_future is None:
            return True
        else:
            return all(
                [
                    future.done()
                    for future in self.kafka_topic_to_future.values()
                ]
            )
class AbstractDataset(abc.ABC):
    @classmethod
    def from_config(
        cls: type, name: str, config: dict[str, Any]
    ) -> AbstractDataset:
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

    def read(self) -> Any:
        """Read the dataset."""
        try:
            return self._read()
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to read dataset {self.name}."
            raise DatasetError(message) from e

    def write(self) -> None:
        """Write the dataset."""
        try:
            return self._write()
        except DatasetError:
            raise
        except Exception as e:
            message = f"Failed to write dataset {self.name}."
            raise DatasetError(message) from e

    def create(self) -> None:
        """Create the dataset."""
        try:
            return self._create()
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
