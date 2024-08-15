from typing import List, Dict, Any
from fastapi import FastAPI, Path
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from pydantic import BaseModel, Field, validator
from neo4j import GraphDatabase
from enum import Enum
from os import getenv

AURA_CONNECTION_URI = getenv("AURA_URI")
AURA_USERNAME = getenv("AURA_USERNAME")
AURA_PASSWORD = getenv("AURA_PASSWORD")

driver = GraphDatabase.driver(
    AURA_CONNECTION_URI,
    auth=(AURA_USERNAME, AURA_PASSWORD)
)


###
# Schema Models
class AreaName(str, Enum):
    """
    Valid AreaModel name strings
    """
    test_buildings = 'Test Buildings'
    east_bank = 'East Bank'


class AreaModel(BaseModel):
    """
    Represents an area
    """
    name: AreaName = Field(..., description="The name of the area")
    thumbnail: str = Field(..., description="The filename of the area's thumbnail image")


class BuildingEntryModel(BaseModel):
    """
    Represents an entire building
    """
    buildingName: str = Field(..., description="The name of the building")
    thumbnail: str = Field(..., description="The filename of the building's thumbnail image")
    keyID: str = Field(..., description="The navID of the building's BuildingKey node")


class NavigationNodeModel(BaseModel):
    """
    Represents a single "step" of a navigation route
    """
    buildingName: str = Field(..., description="The name of the building the node belongs to")
    floor: str = Field(..., description="The floor in the building this navigation node is in")
    navID: str = Field(..., description="The navID of the Neo4j node the model represents")
    thumbnail: str = Field(..., description="The filename of the node's building's thumbnail image")

    # Neo4j returns ints for numeric floors, validator converts those to strings
    @validator('floor', pre=True)
    def validate_floor(cls, v):
        if isinstance(v, int):
            return str(v)
        else:
            return v


###
# Server initialization
areas = [
    AreaModel(name=AreaName.test_buildings.value, thumbnail="test_buildings.png"),
    AreaModel(name=AreaName.east_bank.value, thumbnail="east_bank.jpg"),
]

app = FastAPI(
    title="GopherMaps API",
    summary="REST API for the GopherMaps Project",
    version="0.0.1",
    contact={
        "name": "Ryan Roche",
        "url": "https://socialcoding.net"
    },
    docs_url=None,
    redoc_url=None,
    servers=[{
        "url": "https://api.gophermaps.xyz",
        "description": "The production API server."
    }]
)


###
# Startup/Shutdown Logic
@app.on_event("startup")
async def startup():
    driver.verify_authentication()


@app.on_event("shutdown")
async def shutdown():
    # Close the Neo4j driver connection
    driver.close()


###
# Documentation pages
@app.get("/docs", include_in_schema=False)
async def swagger_override():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="GopherMaps API Docs",
        swagger_favicon_url="https://raw.githubusercontent.com/ryan-roche/gophermaps-data/main/favicon/favicon.ico"
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_override():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="GopherMaps API Docs",
        redoc_favicon_url="https://raw.githubusercontent.com/ryan-roche/gophermaps-data/main/favicon/favicon.ico"
    )

###
# API Endpoints
@app.get("/areas", tags=["Buildings"], operation_id="getAreas")
async def get_areas() -> list[AreaModel]:
    """
    Get all available areas
    """
    return areas


@app.get("/buildings/{area}", tags=["Buildings"], operation_id="getBuildingsForArea")
async def get_buildings_by_area(
        area: AreaName = Path(..., description="The label name of the requested area")
) -> List[BuildingEntryModel]:
    """
    Get all the buildings in a given area
    """
    with driver.session() as session:
        query = """
        MATCH (n:BuildingKey {area: $areaName}) RETURN n
        """
        parameters = {"areaName": area}
        result = session.run(query, parameters)

        results: List[Dict[str, Any]] = result.data()

        # Use list comprehension to unwrap nodes and create BuildingEntryModel instances
        building_entries: List[BuildingEntryModel] = [
            BuildingEntryModel(**record['n']) for record in results
        ]

        return building_entries


@app.get("/destinations/{building}", tags=["Routing"], operation_id="getDestinationsForBuilding")
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


@app.get("/routes/{start}-{end}", tags=["Routing"], operation_id="getRoute")
async def get_route(
        start: str = Path(..., description="The navID of the start building's BuildingKey node"),
        end: str = Path(..., description="The navID of the end building's BuildingKey node")
) -> List[NavigationNodeModel]:
    """
    Get a route between two buildings
    """
    with driver.session() as session:
        query = """
            MATCH (startNode {navID: $start}), (endNode {navID: $end}), path = shortestPath((startNode)-[*]-(endNode))
            RETURN nodes(path)
            """
        parameters = {'start': start, 'end': end}
        result = session.run(query, parameters)

        body: List[Dict[str, Any]] = result.data()
        nodes = body[0]['nodes(path)']

        node_list = [NavigationNodeModel(**node) for node in nodes]

        return node_list
