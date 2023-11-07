# {{cookiecutter.project_name}}

An example pipeline

## Setup development environment

```
poetry install
```

## Running the pipeline

First, make sure that docker is running and run the required docker services in the background

```
aineko service start
```

Then start the pipeline using
```
aineko run ./conf/pipeline.yml
```

## Observe the pipeline

To view the data flowing in the datasets

```
aineko stream --dataset test_sequence
```

To view all data in the dataset, from the start

```
aineko stream --dataset test_sequence --from-beginning
```


## Taking down a pipeline

In the terminal screen running the pipeline, you can press `ctrl-c` to stop execution.

Clean up background services
```
aineko service stop
```
