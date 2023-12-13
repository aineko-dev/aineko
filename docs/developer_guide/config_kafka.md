# Configuring Kafka

Aineko uses [`kafka`](https://kafka.apache.org/documentation/) under the hood for sending messages between nodes. As part of running Aineko locally, it's recommended to run a local `kafka` and `zookeeper` server using

:   
    ```bash
    poetry run aineko service start
    ```

To use a different `kafka` cluster, such as in deployment settings, Aineko allows for configuring of `kafka` parameters through environment variables. Typically, you would want to modify configuration for the [consumer](https://kafka.apache.org/documentation/#consumerconfigs) and [producer](https://kafka.apache.org/documentation/#producerconfigs) to point to the desired cluster.

See below for default `kafka` configuration that ships with `aineko` and how to override them.

::: aineko.config
    options:
        members:
            - DEFAULT_KAFKA_CONFIG
