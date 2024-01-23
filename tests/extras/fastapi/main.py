# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
from fastapi import FastAPI

from aineko.extras.fastapi import consumers, producers

app = FastAPI()


@app.get("/next", status_code=200)
async def query():
    msg = consumers["messages"].next()
    return msg


@app.get("/last", status_code=200)
async def assignment():
    msg = consumers["messages"].consume(how="last", timeout=1)
    return msg


@app.get("/produce", status_code=200)
async def produce():
    producers["messages"].produce({"value": 1})
    producers["messages"].produce({"value": 2})
    producers["messages"].produce({"value": 3})
    return
