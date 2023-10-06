# Contributing to Aineko

Thank you for your interest in contributing to [Aineko](https://github.com/aineko-dev/aineko)!&#x20;

Here are the steps to get started quickly:&#x20;

**Step 1: Install Aineko from source**

```
# install poetry 
curl -sSL https://install.python-poetry.org | python3 -

git clone https://github.com/aineko-dev/aineko

cd aineko && poetry install 
```

We highly encourage you to validate your changes by testing E2E. This means to validate the changes with your pipeline by pointing `aineko` to the dev folder.&#x20;

**Step 2: Have your own pipeline or create one**&#x20;

```
# using poetry is important so that we are actually invoking the dev version of Aineko
poetry run aineko create 

```

**Step 3: Go to `pyproject.toml` and apply the following changes:**&#x20;

```
-aineko = "^0.1.3"
+aineko = { path = "<path/to/aineko/git/repo>", develop=true}
```

**Step 4: Test your changes - did it work?**&#x20;



**Step 5:**&#x20;

Finally, after you have make all the changes, it is good to validate that you adhered to our style guide and you did not break anything.  &#x20;

```
# Within aineko git repository
make lint 
make unit-test
make integration-test
```

**Step 6: Push and see you on Github!**&#x20;
