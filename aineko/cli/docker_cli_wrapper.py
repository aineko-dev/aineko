"""A wrapper class that executes Docker CLI commands via subprocess."""
import subprocess
from typing import Optional
import os


class DockerCLIWrapper:
    """A wrapper class that executes Docker CLI commands via subprocess.

    This class provides methods to start, stop, and restart Docker services 
    using docker-compose.

    Methods:
        start_service(cls, path: Optional[str]) -> None:
            Start a Docker service using the specified Docker Compose file.

        stop_service(cls, path: Optional[str]) -> None:
            Stop a running Docker service specified in the Docker Compose file.

        restart_service(cls, path: Optional[str]) -> None:
            Restart a running Docker service specified in the Docker 
            Compose file.

    """

    DEFAULT_RELATIVE_PATH: str = "kafka/docker-compose.yml"

    @classmethod
    def start_service(cls, path: Optional[str]) -> None:
        """Start a Docker service using the specified Docker Compose file.

        Args:
            path (Optional[str]): The path to the Docker Compose file. 
            If not provided, the default path is used.

        Returns:
            None

        """
        absolute_docker_file_path = cls._resolve_optional_relative_path(path)
        try:
            cls._validate_docker_compose_file(absolute_docker_file_path)
        except FileNotFoundError as ex:
            print(str(ex))
            return

        command = f"docker-compose -f {absolute_docker_file_path} up -d"
        try:
            output = subprocess.check_output(
                command, shell=True, text=True, stderr=subprocess.STDOUT
            )
            print(output)
        except subprocess.CalledProcessError as ex:
            print(f"Error: {ex}")
            print(f"Command Output: {ex.output}")

    @classmethod
    def stop_service(cls, path: Optional[str]) -> None:
        """Stop a running Docker service specified in the Docker Compose file.

        Args:
            path (Optional[str]): The path to the Docker Compose file. 
            If not provided, the default path is used.

        Returns:
            None

        """
        absolute_docker_file_path = cls._resolve_optional_relative_path(path)
        try:
            cls._validate_docker_compose_file(absolute_docker_file_path)
        except FileNotFoundError as ex:
            print(str(ex))
            return

        command = f"docker-compose -f {absolute_docker_file_path} stop"
        try:
            output = subprocess.check_output(
                command, shell=True, text=True, stderr=subprocess.STDOUT
            )
            print(output)
        except subprocess.CalledProcessError as ex:
            print(f"Error: {ex}")
            print(f"Command Output: {ex.output}")

    @classmethod
    def restart_service(cls, path: Optional[str]) -> None:
        """Restart a running Docker service specified in the Docker 
        Compose file.

        Args:
            path (Optional[str]): The path to the Docker Compose file. 
            If not provided, the default path is used.

        Returns:
            None

        """
        absolute_docker_file_path = cls._resolve_optional_relative_path(path)
        try:
            cls._validate_docker_compose_file(absolute_docker_file_path)
        except FileNotFoundError as ex:
            print(str(ex))
            return

        command = f"docker-compose -f {absolute_docker_file_path} restart"
        try:
            output = subprocess.check_output(
                command, shell=True, text=True, stderr=subprocess.STDOUT
            )
            print(output)
        except subprocess.CalledProcessError as ex:
            print(f"Error: {ex}")
            print(f"Command Output: {ex.output}")

    @classmethod
    def _resolve_optional_relative_path(cls, path: Optional[str]) -> str:
        """Resolve the optional relative path to an absolute path.

        Args:
            path (Optional[str]): The optional relative path.

        Returns:
            str: The absolute path to the Docker Compose file.

        """
        if path is None:
            print(
                f"No path provided, defaulting to {cls.DEFAULT_RELATIVE_PATH}"
            )
            absolute_docker_file_path = os.path.abspath(
                cls.DEFAULT_RELATIVE_PATH
            )
        else:
            absolute_docker_file_path = os.path.abspath(path)

        return absolute_docker_file_path

    @staticmethod
    def _validate_docker_compose_file(absolute_docker_file_path: str) -> None:
        """Validate if the specified file is a valid Docker Compose file.

        Args:
            absolute_docker_file_path (str): The absolute path to
            the Docker Compose file.

        Raises:
            FileNotFoundError: If the file does not exist or if it is not a
                docker-compose.yml file.

        Returns:
            None

        """
        if not os.path.isfile(absolute_docker_file_path):
            raise FileNotFoundError(
                f"File {absolute_docker_file_path} does not exist"
            )

        if not absolute_docker_file_path.endswith("docker-compose.yml"):
            raise FileNotFoundError(
                f"File {absolute_docker_file_path} must be a"
                " docker-compose.yml file"
            )
