from fastapi import FastAPI
from pydantic import BaseModel
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

if not load_dotenv(dotenv_path="/docker-entrypoint.d/.env"):
    raise Exception("Could not load .env file")

URI = "bolt://db:7687"
AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD"))

driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()

app = FastAPI(docs_url="/docs")


class BuildingEntryModel(BaseModel):
    name: str
    thumbnail: str
    navID: str


@app.get("/areas")
# TODO: Cache areas query after first run since it won't be changing
async def get_areas():
    return driver.execute_query(
        'MATCH(n) UNWIND labels(n) AS label WITH DISTINCT label WHERE label '
                                                  '<> "Building" RETURN label'
    ).records


@app.get("/buildings/{area}")
async def get_buildings_by_area(area, response_model=BuildingEntryModel):
    records =  driver.execute_query(
        f"MATCH (n:{str(area)}:BuildingKey) RETURN n",
    ).records

    return [record[0] for record in records]


@app.get("/destinations/{building_id}")
async def get_destinations_for_building(building_id: str):
    records = driver.execute_query(
        """
        MATCH (startNode {navID: $inputNodeID}), (reachableNode:BuildingKey)
        WHERE (startNode)-[*]-(reachableNode)
        RETURN reachableNode
        """,
        inputNodeID=building_id
    ).records

    return [record[0] for record in records]


@app.get("/routes/{start}-{end}")
async def get_route(start: str, end: str):
    # Query the neo4j database and return an array of node id strings
    records = driver.execute_query(
        """
        MATCH (startNode {navID: $start}), (endNode {navID: $end}), path = shortestPath((startNode)-[*]-(endNode))
        RETURN nodes(path)
        """,
        start=start,
        end=end
    ).records

    return records[0][0]
