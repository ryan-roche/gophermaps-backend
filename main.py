from fastapi import FastAPI, Path
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
from enum import Enum


URI = "neo4j+s://3be5622e.databases.neo4j.io"
AUTH = ("neo4j", "Cd5eIf6EXhO645obqSAGv4Dd4WitBuKo3UW1_E_GMuI") # TODO REMOVE FROM CODE

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
async def get_areas() -> list[str]:
    """
    Get all available area labels
    """
    records = driver.execute_query(
        """MATCH (n)
        UNWIND labels(n) AS label
        WITH DISTINCT label
        WHERE NOT label IN ["Building", "BuildingKey"]
        RETURN label"""
    ).records

    return [record[0] for record in records]


@app.get("/buildings/{area}", tags=["Buildings"])
async def get_buildings_by_area(
        area: AreaName = Path(..., description="The label name of the requested area")
) -> list[BuildingEntryModel]:
    """
    Get all the areas in a given area
    """
    records = driver.execute_query(
        f"MATCH (n:{str(area)}:BuildingKey) RETURN n",
    ).records

    return [record[0] for record in records]


@app.get("/destinations/{building_id}", tags=["Routing"])
async def get_destinations_for_building(
        building_id: str = Path(..., description="The navID of the building whose destinations are being requested")
):
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
async def get_route(
        start: str = Path(..., description="The navID of the start building's BuildingKey node"),
        end: str = Path(..., description="The navID of the end building's BuildingKey node")
) -> list[NavigationNodeModel]:
    """
    Get a route between two buildings
    """
    records = driver.execute_query(
        """
        MATCH (startNode {navID: $start}), (endNode {navID: $end}), path = shortestPath((startNode)-[*]-(endNode))
        RETURN nodes(path)
        """,
        start=start,
        end=end
    ).records

    return records[0][0]
