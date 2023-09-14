import subprocess
from typing import Optional 
import os 

DEFAULT_RELATIVE_PATH = "kafka/docker-compose.yml"

class DockerCLIWrapper(object): 
    """A wrapper class that executes Docker cli commands via subprocess
    """
    
    DEFAULT_RELATIVE_PATH: str = "kafka/docker-compose.yml"

    @classmethod
    def start_service(cls, path: Optional[str]) -> None:
        absolute_docker_file_path = cls._resolve_optional_relative_path(path)
        try: 
            cls._validate_docker_compose_file(absolute_docker_file_path)

        except Exception as e: 
            print(str(e))
            return

        command = f"docker-compose -f {absolute_docker_file_path} up -d"
        try:
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            print(output)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    @classmethod
    def stop_service(cls, path: Optional[str]) -> None:
        absolute_docker_file_path = cls._resolve_optional_relative_path(path)
        try: 
            cls._validate_docker_compose_file(absolute_docker_file_path)

        except Exception as e: 
            print(str(e))
            return

        command = f"docker-compose -f {absolute_docker_file_path} stop"
        try:
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            print(output)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    @classmethod
    def restart_service(cls, path: Optional[str]) -> None:
        absolute_docker_file_path = cls._resolve_optional_relative_path(path)
        try: 
            cls._validate_docker_compose_file(absolute_docker_file_path)

        except Exception as e: 
            print(str(e))
            return

        command = f"docker-compose -f {absolute_docker_file_path} restart"
        try:
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            print(output)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")


    @classmethod
    def _resolve_optional_relative_path(cls, path: Optional[str]) -> str: 
        if path is None:
            print(f"No path provided, defaulting to {cls.DEFAULT_RELATIVE_PATH}")
            absolute_docker_file_path = os.path.abspath(cls.DEFAULT_RELATIVE_PATH)
        else:
            absolute_docker_file_path = os.path.abspath(path)

        return absolute_docker_file_path
    
    def _validate_docker_compose_file(absolute_docker_file_path: str) -> None: 
        """
        throws if it is not a valid docker-compose file 
        """
        if not os.path.isfile(absolute_docker_file_path):
            raise FileNotFoundError(f"File {absolute_docker_file_path} does not exist")
        
        if not absolute_docker_file_path.endswith("docker-compose.yml"):
            raise FileNotFoundError(f"File {absolute_docker_file_path} must be a docker-compose.yml file")

        return