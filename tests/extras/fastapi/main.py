# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
from fastapi import FastAPI

from aineko.extras.fastapi import inputs, outputs

app = FastAPI()


@app.get("/next", status_code=200)
async def query():
    msg = inputs["messages"].next()
    return msg


@app.get("/last", status_code=200)
async def assignment():
    msg = inputs["messages"].read(how="last", timeout=1)
    return msg


@app.get("/produce", status_code=200)
async def produce():
    outputs["messages"].write(1)
    outputs["messages"].write(2)
    outputs["messages"].write(3)
    return
