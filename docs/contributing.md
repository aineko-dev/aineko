# Contributing to Aineko

Thank you for your interest in contributing to [Aineko](https://github.com/aineko-dev/aineko)!&#x20;

Here are the steps to get started quickly:&#x20;

**Step 1: Install Aineko from source**

```bash
# install poetry
curl -sSL https://install.python-poetry.org | python3 -

git clone https://github.com/aineko-dev/aineko

cd aineko && poetry install
```

**Step 2: Make your changes to Aineko**&#x20;

**Step 3: Have your own pipeline or create one**&#x20;

We highly encourage you to validate your changes by testing E2E. This means to validate the changes with your pipeline by pointing `aineko` to the dev folder.&#x20;

```bash
# using poetry is important so that we are actually invoking the dev version of Aineko

poetry run aineko create
```

**Step 4: Go to `pyproject.toml` and apply the following changes:**&#x20;

This will ensure your aineko is pointing to the repository you made changes to

```bash
-aineko = "^0.2.3"
+aineko = { path = "<path/to/aineko/git/repo>", develop=true}
```

**Step 5: Test your changes - did it work?**&#x20;

**Step 6: Run lints and tests**&#x20;

Finally, after you have make all the changes, it is good to validate that you adhered to our style guide and you did not break anything.  &#x20;

```bash
# Within aineko git repository
make lint
make unit-test
make integration-test
```

**Step 7: Push, make a PR and see you on Github!**&#x20;
