# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
from fastapi import FastAPI

app = FastAPI()


@app.get("/hello-world", status_code=200)
async def query():
    return "Hello World!"
