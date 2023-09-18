import subprocess
from typing import Optional 
import os 


class KafkaCLIWrapper(object): 
    @classmethod
    def view_dataset(cls, dataset_name: str) -> None:

        command = f"docker exec -it broker kafka-console-consumer --bootstrap-server localhost:9092 --topic {dataset_name} --from-beginning"
        try:
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            print(output)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    @classmethod
    def stream_dataset(cls, dataset_name: str) -> None:

        command = f"docker exec -it broker kafka-console-consumer --bootstrap-server localhost:9092 --topic {dataset_name}"
        try:
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
            print(output)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")