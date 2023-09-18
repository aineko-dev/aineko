import subprocess
from typing import Optional
import os


class KafkaCLIWrapper(object):
    @classmethod
    def consume_kafka_topic(cls, topic_name: str, from_beginning: bool) -> None:
        if from_beginning:
            command = f"docker exec -it broker kafka-console-consumer --bootstrap-server localhost:9092 --topic {topic_name} --from-beginning"
        else: 
            command = f"docker exec -it broker kafka-console-consumer --bootstrap-server localhost:9092 --topic {topic_name}"
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line-buffered
                universal_newlines=True,
            )
            for line in process.stdout:
                print(line.strip())

            process.wait()
        except subprocess.CalledProcessError as e:
            print(f"Error running Kafka viewer: {e}")
            print(f"Command output: {e.output}")

    