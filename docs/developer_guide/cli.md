# CLI documentation

The Aineko CLI is a development tool that allows you to get started quickly and introspect your pipeline runs more expediently.

::: mkdocs-click
    :module: aineko.__main__
    :command: cli
    :depth: 1

## Shell completion

Aineko supports shell completion for Bash and Zsh. To enable it, follow the instructions below.

!!! info "Please select your shell"

    === "Bash"
        Add this to `~/.bashrc`:


        ```bash
        eval "$(_AINEKO_COMPLETE=bash_source aineko)"
        ```

    === "Zsh"
        Add this to `~/.zshrc`:


        ```bash
        eval "$(_AINEKO_COMPLETE=zsh_source aineko)"
        ```
