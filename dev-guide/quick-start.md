---
description: Fastest way to get a pipeline up and running
---

# Quick Start

### Technical Dependencies&#x20;

1. Docker&#x20;
2. Poetry (a python package manager)&#x20;
3. Python >= 3.10&#x20;

### Steps

**Step 1: Install Aineko**&#x20;

Install virtual environment. Optional step, but a best practice to isolate dependencies installed.&#x20;

```
python -m venv venv 
source venv/bin/activate 
pip install aineko

```

**Step 2: Create a pipeline with aineko cli**&#x20;

```
aineko create 
```

**Step 3: Install depdencies in the new pipeline**&#x20;

```
cd my-awesome-pipeline
poetry install 
```

**Step 4:**&#x20;

```
poetry run aineko run -c ./conf/pipeline.yaml
```
