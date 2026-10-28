from fastapi import FastAPI
from models import Item, Measure, ProgramCost

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/measures")
async def create_measure(measure: Measure):
    return measure


@app.post("/program_costs")
async def create_program_cost(program_cost: ProgramCost):
    return program_cost


@app.post("/items/")
async def create_item(item: Item):
    return item
