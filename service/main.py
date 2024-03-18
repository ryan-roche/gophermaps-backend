from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(docs_url="/docs")


class BuildingEntryModel(BaseModel):
    area: str
    name: str
    thumb: str


@app.get("/areas")
async def get_areas():
    areas = ["TestBuildings"]
    return areas


@app.get("/buildings/{area}")
async def get_buildings_by_area(area):
    # TODO query neo4j database for buildings with area tag
    return ["Test 1", "Test 2", "Test 3"]


@app.get("/destinations/{building}")
async def get_destinations_for_building(building: str):
    # TODO query neo4j database and return an array of building names
    return {"message": f"Destinations for {building}"}


@app.get("/routes/{start}-{end}")
async def get_route(start: str, end: str):
    # Query the neo4j database and return an array of node id strings
    return {"message": f"Start node id is {start} and end node id is {end}"}
