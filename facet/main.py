from fastapi import FastAPI

from models import Measure, Item

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/test/{input_integer}")
async def root(input_integer: int):
    return {
            "input": input_integer,
            "product_2": input_integer * 2,
    }

@app.post("/measures")
async def create_measure(measure: Measure):
    return measure

@app.post("/items/")
async def create_item(item: Item):
    return item