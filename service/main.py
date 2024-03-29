from fastapi import FastAPI, Path
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
from dotenv import load_dotenv
from enum import Enum
import os
import string

if not load_dotenv(dotenv_path="/docker-entrypoint.d/.env"):
    raise Exception("Could not load .env file")

URI = "bolt://db:7687"
AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD"))

driver = GraphDatabase.driver(URI, auth=AUTH)
driver.verify_connectivity()


class BuildingEntryModel(BaseModel):
    """
    Represents an entire building
    """
    name: str = Field(..., description="The name of the building")
    thumbnail: str = Field(..., description="The filename of the building's thumbnail image")
    navID: str = Field(..., description="The navID of the building's BuildingKey node")


class NavigationNodeModel(BaseModel):
    """
    Represents a single "step" of a navigation route
    """
    name: str = Field(..., description="The name of the building the node belongs to")
    navID: str = Field(..., description="The navID of the Neo4j node the model represents")


class AreaName(str, Enum):
    test_buildings = 'TestBuildings'
    east_bank = 'EastBank'


app = FastAPI(docs_url="/docs")


@app.get("/areas", tags=["Buildings"])
# TODO: Cache areas query after first run since it won't be changing
async def get_areas() -> list[str]:
    """
    Get all available area labels
    """
    # TODO: Add parameter and response descriptions
    records = driver.execute_query(
        """MATCH (n)
        UNWIND labels(n) AS label
        WITH DISTINCT label
        WHERE NOT label IN ["Building", "BuildingKey"]
        RETURN label"""
    ).records

    return [record[0] for record in records]


@app.get("/buildings/{area}", tags=["Buildings"])
async def get_buildings_by_area(area: AreaName) -> list[BuildingEntryModel]:
    """
    Get all the areas in a given area
    """
    # TODO: Add parameter and response descriptions
    records = driver.execute_query(
        f"MATCH (n:{str(area)}:BuildingKey) RETURN n",
    ).records

    return [record[0] for record in records]


@app.get("/destinations/{building_id}", tags=["Routing"])
async def get_destinations_for_building(building_id: str = Path(..., description="The navID of the building whose destinations are being requested")):
    """
    Get the destinations reachable from a given building
    """
    # TODO: Add parameter and response descriptions
    records = driver.execute_query(
        """
        MATCH (startNode {navID: $inputNodeID}), (reachableNode:BuildingKey)
        WHERE (startNode)-[*]-(reachableNode)
        RETURN reachableNode
        """,
        inputNodeID=building_id
    ).records

    return [record[0] for record in records]


@app.get("/routes/{start}-{end}", tags=["Routing"])
async def get_route(start: str, end: str) -> list[NavigationNodeModel]:
    """
    Get a route between two buildings
    @param start: The navID of the BuildingKey node for the starting building
    @param end: The navID of the BuildingKey node for the destination building
    @return: An ordered list of the nodes that must be traversed to get from start to end. The navIDs of these nodes can
    be used to get the corresponding instruction files for moving between those nodes.
    """
    # TODO: Add parameter and response descriptions
    records = driver.execute_query(
        """
        MATCH (startNode {navID: $start}), (endNode {navID: $end}), path = shortestPath((startNode)-[*]-(endNode))
        RETURN nodes(path)
        """,
        start=start,
        end=end
    ).records

    return records[0][0]
