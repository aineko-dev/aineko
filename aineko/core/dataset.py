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
from typing import Any, Dict, Generic, List, Optional, TypeVar

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

    A dataset comprises 2 subcomponents, the query layer and the storage layer.
    The storage layer refers to the actual storage infrastructure that holds the
    data, and the query layer is an API layer that allows for the interaction
    with the storage layer.

    The `AbstractDataset` class provides a common interface for all dataset
    implementations. All dataset implementations must subclass the
    `AbstractDataset` class and must implement the following methods:

    * `__init__`: Initialize the dataset object.
    * `create`: Creation of the actual storage layer.
    * `delete`: Delete the storage layer.
    * `exists`: Check if the storage layer exists.
    * `initialize`: Initialize the query layer.
    * `read`: Read an entry from the dataset by querying the storage layer.
    * `write`: Write an entry to the dataset by querying the storage layer.
    * `setup_test_mode`: Set up the dataset for testing.

    Please refer to the method docstrings for more information on the
    implementation details of each method.
    """

    name: str

    _test: bool
    _input_values: List[Dict]
    _output_values: List[Dict]

    @abc.abstractmethod
    def __init__(
        self,
        name: str,
        params: Dict[str, Any],
        test: bool = False,
    ) -> None:
        """Subclass implementation to initialize the dataset object.

        All dataset implementations must implement the `__init__` method.
        A dataset object should be initialized with the following attributes:

        * `self.name`: The name of the dataset.
        * `self.params`: A dictionary of parameters.
        * `self._test`: Whether the dataset is in test mode.

        Args:
            name: The name of the dataset.
            params: A dictionary of parameters.
            test: Whether the dataset should be initialized in test mode.
        """
        raise NotImplementedError

    def __str__(self) -> str:
        """Return the string representation of the dataset."""
        return f"{self.__class__.__name__}({self.name})"

    @classmethod
    def from_config(
        cls, name: str, config: Dict[str, Any], test: bool = False
    ) -> "AbstractDataset":
        """Create a dataset from a configuration dictionary.

        Args:
            name: The name of the dataset.
            config: The configuration dictionary.
            test: Whether the dataset should be initialized in test mode.

        Returns:
            Instance of an `AbstractDataset` subclass.

        Example:
            In some cases, it is necessary to dynamically create a dataset from
            a configuration dictionary. Since the dataset type could be any
            dataset implementation, the `from_config` method provides a way to
            properly initialize the dataset object.

            ```python
            config = {
                "type": "aineo.datasets.kafka.KafkaDataset",
                "location": "localhost:9092",
                "params": {
                    "param_1": "bar"
                }
            }
            dataset = AbstractDataset.from_config("my_dataset", config)
            ```
        """
        dataset_config = DatasetConfig(**dict(config))

        class_obj = import_from_string(dataset_config.type, kind="class")
        class_instance = class_obj(name, dict(dataset_config), test=test)
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
        """Subclass implementation to create the dataset storage layer."""
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, *args: T, **kwargs: T) -> Any:
        """Subclass implementation to delete the dataset storage layer."""
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

    @abc.abstractmethod
    def setup_test_mode(
        self,
        source_node: str,
        source_pipeline: str,
        input_values: Optional[List[dict]] = None,
    ) -> None:
        """Subclass implementation to set up the dataset for testing.

        Nodes have the ability to run in test mode, which allows them to run
        without setting up the actual dataset storage layer. All dataset
        implementations must implement this method. A dataset in test mode
        should never interact with the real storage layer. Instead, it should
        use the class attributes as the storage layer:

        * `_input_values` for input values
        * `_output_values` for output values

        Args:
            source_node: The name of the source node.
            source_pipeline: The name of the source pipeline.
            input_values: A list of input values.
        """
        raise NotImplementedError

    def get_test_input_values(self) -> List[Dict]:
        """Return the input values used for testing.

        Returns:
            A list of input values.

        Raises:
            DatasetError: If the dataset is not in test mode.
        """
        if self._test:
            return self._input_values

        raise DatasetError("Dataset is not in test mode.")

    def get_test_output_values(self) -> List[Dict]:
        """Return the output values used for testing.

        Returns:
            A list of output values.

        Raises:
            DatasetError: If the dataset is not in test mode.
        """
        if self._test:
            return self._output_values

        raise DatasetError("Dataset is not in test mode.")

    def test_is_empty(self) -> bool:
        """Return whether the dataset is empty.

        Returns:
            True if the dataset is empty, otherwise False.

        Raises:
            DatasetError: If the dataset is not in test mode.
        """
        if self._test:
            if len(self._input_values) == 0:
                return True
            return False

        raise DatasetError("Dataset is not in test mode.")
