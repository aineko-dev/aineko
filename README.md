# Aineko

Aineko is a Python framework for building data applications.

With Aineko, you seamlessly bring data into any product and iterate quickly. Whether you're an individual developer or part of a larger team, Aineko helps you rapidly build scalable, maintainable, and fast data applications.

Under the hood, Aineko automatically configures tooling needed for production-ready data apps, like message brokers, distributed compute, and more. This allows you to focus on building your application instead of spending time with configuration and infrastructure.

## Documentation

For full documentation visit: https://docs.aineko.dev/

## Quick Start

### Technical Dependencies

1. [Docker](https://www.docker.com/get-started/)
2. [Poetry](https://python-poetry.org/docs/#installation) (a python dependency manager)
3. [Python](https://www.python.org/downloads/) (version 3.10)

### Steps

**Step 1: Install Aineko**

Install virtual environment. Optional step, but a best practice to isolate dependencies installed.

```
python -m venv venv
source venv/bin/activate
pip install aineko
```

**Step 2: Create a template pipeline with aineko cli**

```
aineko create
```

You will see the following prompts as `aineko` tries to create a project directory containing the boilerplate you need for a pipeline. Feel free to use the defaults suggested!

```
  [1/5] project_name (My Awesome Pipeline):
  [2/5] project_slug (my_awesome_pipeline):
  [3/5] project_description (Behold my awesome pipeline!):
  [4/5] authors (John Doe <johndoe@gmail.com>):
  [5/5] pipeline_slug (test-aineko-pipeline):
```

**Step 3: Install dependencies in the new pipeline**

```
cd my_awesome_pipeline
poetry install
```

**Step 4: Start the Aineko background services**

```
aineko run ./conf/pipeline.yml
```

**Step 5: Start the template pipeline**

```
aineko run ./conf/pipeline.yml
```

## Examples

To see some examples of Aineko in action visit: https://docs.aineko.dev/examples

- [Aineko Dream](https://github.com/aineko-dev/aineko-dream)
- More coming soon...

## Contributing

If you're interested in contributing to Aineko, follow this guide: https://docs.aineko.dev/contributing-to-aineko
