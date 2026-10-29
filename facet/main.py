from fastapi import FastAPI
from models import Item, Measure, ProgramCost

app = FastAPI()

THERM_CONVERSION = 29.307111111


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/measures")
async def create_measure(measure: Measure):
    return measure


@app.post("/calculate_savings")
async def calculate_savings(measure: Measure):

    LifecycleNetkWh = (
        measure.num_units
        * (measure.ntgr_therm + 0)
        * measure.eul_yrs
        * measure.installation_rate_kwh
        * measure.realization_rate_kwh
        * (measure.unit_kwh_1st_baseline + measure.unit_kwh_iou_water_1st_baseline)
    )

    LifecycleNetkWhSite = (
        measure.num_units
        * (measure.ntgr_therm + 0)
        * measure.eul_yrs
        * measure.installation_rate_kwh
        * measure.realization_rate_kwh
        * measure.unit_kwh_1st_baseline
    )

    LifecycleNetkWhWater = (
        measure.num_units
        * (measure.ntgr_therm + 0)
        * measure.eul_yrs
        * measure.installation_rate_kwh
        * measure.realization_rate_kwh
        * measure.unit_kwh_iou_water_1st_baseline
    )

    LifecycleNetTherms = (
        measure.num_units
        * (measure.ntgr_therm + 0)
        * measure.eul_yrs
        * measure.installation_rate_therm
        * measure.realization_rate_therm
        * measure.unit_therm_1st_baseline
    )

    return {
        "LifecycleNetkWh": LifecycleNetkWh,
        "LifecycleNetkWhSite": LifecycleNetkWhSite,
        "LifecycleNetkWhWater": LifecycleNetkWhWater,
        "LifecycleNetTherms": LifecycleNetTherms,
    }


@app.post("/program_costs")
async def create_program_cost(program_cost: ProgramCost):
    return program_cost


@app.post("/items/")
async def create_item(item: Item):
    return item
