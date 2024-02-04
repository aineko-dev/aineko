# Aineko Dream

Aineko Dream leverages the power of generative AI to create a starter Aineko pipeline based on your use case. 

## Generating a Project

To generate a project, invoke the Aineko Dream CLI with a prompt with:

```bash
poetry run aineko dream create --api-key API_KEY "create a pipeline that scrapes twitter and analyses the results to identify trends"
```

replacing `API-KEY` with a valid Aineko Dream API key. Contact support@aineko.dev to get an API key to try this feature.

Aineko Dream goes on to create a complete aineko project, including node code, pipeline configuration and more using OpenAI's GPT-4 models. Upon completion, Aineko Dream publishes the project in the public GitHub repository [dream-catcher](https://github.com/Convex-Labs/dream-catcher).

## Creating your Aineko Dream project

Upon completion of the previous step, `aineko create` offers an easy way to get started. To initialize an aineko project using the generated files from the previous step, run

```bash
poetry run aineko create --repo Convex-Labs/dream-catcher#12345
```

where the argument after `--repo` should be the unique ID associated to your generated project. This will be output in the result of the previous section.

## Checking on the status of your Aineko Dream request

After sending a request to the Aineko Dream CLI, you will be provided with a request ID that looks like `2c8341b7-9cb4-41f1-87ad-f363925fd2fa`. To check on the status of the request, use the following Aineko Dream CLI command:

```bash
poetry run aineko dream check 2c8341b7-9cb4-41f1-87ad-f363925fd2fa
```