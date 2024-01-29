# Copyright 2023 Aineko Authors
# SPDX-License-Identifier: Apache-2.0
from fastapi import FastAPI

from aineko.extras.fastapi import consumers, health_router, producers

app = FastAPI()

app.include_router(health_router)


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
    producers["messages"].produce(1)
    producers["messages"].produce(2)
    producers["messages"].produce(3)
    return
