from typing import List, Dict, Any
from fastapi import FastAPI, Path
from fastapi.openapi.models import Server
from pydantic import BaseModel, Field
from neo4j import GraphDatabase
from enum import Enum
from os import getenv


AURA_CONNECTION_URI = getenv("AURA_URI")
AURA_USERNAME = getenv("AURA_USERNAME")
AURA_PASSWORD = getenv("AURA_PASSWORD")

# Driver object declaration
driver = GraphDatabase.driver(
    AURA_CONNECTION_URI,
    auth=(AURA_USERNAME, AURA_PASSWORD)
)


class BuildingEntryModel(BaseModel):
    """
    Represents an entire building
    """
    buildingName: str = Field(..., description="The name of the building")
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


server1 = Server(url="https://api.gophermaps.xyz", description="Main API Server")

app = FastAPI(docs_url="/docs", servers=[server1])


@app.on_event("startup")
async def startup():
    driver.verify_authentication()


@app.on_event("shutdown")
async def shutdown():
    # Close the Neo4j driver connection
    driver.close()


@app.get("/areas", tags=["Buildings"])
async def get_areas() -> list[str]:
    """
    Get all available area labels
    """
    with driver.session() as session:
        records = session.run(
            """MATCH (n)
            UNWIND labels(n) AS label
            WITH DISTINCT label
            WHERE NOT label IN ["Building", "BuildingKey"]
            RETURN label"""
        )

        return [record[0] for record in records]


@app.get("/buildings/{area}", tags=["Buildings"])
async def get_buildings_by_area(
        area: AreaName = Path(..., description="The label name of the requested area")
) -> List[BuildingEntryModel]:
    """
    Get all the buildings in a given area
    """
    with driver.session() as session:
        result = session.run(
            f"MATCH (n:{area.value}:BuildingKey) RETURN n",
        )

        results: List[Dict[str, Any]] = result.data()

        # Use list comprehension to unwrap nodes and create BuildingEntryModel instances
        building_entries: List[BuildingEntryModel] = [
            BuildingEntryModel(**record['n']) for record in results
        ]

        return building_entries


@app.get("/destinations/{building}", tags=["Routing"])
async def get_destinations_for_building(
        building: str = Path(..., description="The name of the building whose destinations are being queried")
) -> List[BuildingEntryModel]:
    """
    Get the destinations reachable from a given building
    """
    query = """
    MATCH (startNode:BuildingKey {buildingName: $building}), (reachableNode:BuildingKey)
    WHERE (startNode)-[*]-(reachableNode)
    RETURN reachableNode
    """
    parameters = {'building': building}

    with driver.session() as session:
        result = session.run(query, parameters)

        # Assume `results` is the list of dictionaries returned by `session.run`
        results: List[Dict[str, Any]] = result.data()

        # Use list comprehension to unwrap nodes and create BuildingEntryModel instances
        destination_buildings: List[BuildingEntryModel] = [
            BuildingEntryModel(**record['reachableNode']) for record in results
        ]

        return destination_buildings


@app.get("/routes/{start}-{end}", tags=["Routing"])
async def get_route(
        start: str = Path(..., description="The navID of the start building's BuildingKey node"),
        end: str = Path(..., description="The navID of the end building's BuildingKey node")
) -> list[NavigationNodeModel]:
    """
    Get a route between two buildings
    """
    with driver.session() as session:
        records = session.run(
            """
            MATCH (startNode {navID: $start}), (endNode {navID: $end}), path = shortestPath((startNode)-[*]-(endNode))
            RETURN nodes(path)
            """,
            start=start,
            end=end
        )

    return records[0][0]
