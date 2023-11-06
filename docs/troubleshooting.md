# Troubleshooting

## How to install a specific version of Python

We recommend using [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#getting-pyenv) to manage your Python versions. Once you have pyenv installed, you can run the following commands to install Python 3.10.
1. `pyenv install 3.10` to install Python 3.10
2. In your project directory, run the following command to set the local Python version to 3.10: `pyenv local 3.10`
   This will create a `.python-version` file in your project directory which will tell pyenv to (automagically) use Python 3.10 when you're in that directory.
3. Check that you're now using the correct version of Python by running `python --version`. You should see something like `Python 3.10.12`.
4. You're all set! You can now proceed with [step 1](#step-1-install-aineko) of the quick start guide.

Pyenv is a great tool for managing Python versions, but it can be a bit tricky to get it set up correctly. If you're having trouble, check out the [pyenv documentation](https://github.com/pyenv/pyenv?tab=readme-ov-file#usage) or [this tutorial](https://realpython.com/intro-to-pyenv/). If you're still having trouble, feel free to reach out to us on [Slack](https://join.slack.com/t/aineko-dev/shared_invite/zt-23yuq8mrl-uZavRQKGFltxLZLCqcQZaQ)!
