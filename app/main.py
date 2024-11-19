from os import getenv
from enum import Enum
from typing import List, Dict, NamedTuple, Any
from pydantic import BaseModel, Field, validator
from fastapi import FastAPI, Path, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from neo4j import GraphDatabase, graph
from discord_webhook import AsyncDiscordWebhook, DiscordEmbed

AURA_CONNECTION_URI = getenv("AURA_URI")
AURA_USERNAME = getenv("AURA_USERNAME")
AURA_PASSWORD = getenv("AURA_PASSWORD")

DISCORD_WEBHOOK_URL = getenv("DISCORD_WEBHOOK_URL")

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
    # test_buildings = 'Test Buildings'
    east_bank = 'East Bank',
    west_bank = 'West Bank',
    st_paul = 'St Paul Campus'


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
    navID: str = Field(..., description="The navID of the building's BuildingKey node", alias="keyID")

    class Config:
        populate_by_name = True


class NavigationNodeModel(BaseModel):
    """
    Represents a single "step" of a navigation route
    """
    buildingName: str = Field(..., description="The name of the building the node belongs to")
    floor: str = Field(..., description="The floor in the building this navigation node is in")
    navID: str = Field(..., description="The navID of the Neo4j node the model represents")
    image: str = Field(..., description="The reference image for the navigation node")

    # Neo4j returns ints for numeric floors, validator converts those to strings
    @validator('floor', pre=True)
    def validate_floor(cls, v):
        if isinstance(v, int):
            return str(v)
        else:
            return v


class RouteResponseModel(BaseModel):
    """
    Wrapper for responses to getRoute
    """
    pathNodes: List[NavigationNodeModel]
    buildingThumbnails: Dict[str, str]
    instructionsAvailable: Dict[str, bool]


###
# Server initialization
areas = [
    # AreaModel(name=AreaName.test_buildings.value, thumbnail="TestBuildings.jpg"),
    AreaModel(name=AreaName.east_bank.value, thumbnail="EastBank.jpg"),
    AreaModel(name=AreaName.west_bank.value, thumbnail="WestBank.jpg"),
    AreaModel(name=AreaName.st_paul.value, thumbnail="StPaul.jpg")
]

app = FastAPI(
    title="GopherMaps API",
    summary="REST API for the GopherMaps Project",
    version="0.0.2",
    contact={
        "name": "Ryan Roche",
        "url": "https://socialcoding.net"
    },
    docs_url=None,
    redoc_url=None,
    servers=[
        {
            "url": "https://api.gophermaps.xyz",
            "description": "The production API server"
        },
        {
            "url": "http://127.0.0.1:8000",
            "description": "Localhost API server for testing"
        }
    ]
)


###
# Startup/Shutdown Logic
@app.on_event("startup")
async def startup():
    try:
        driver.verify_authentication()
        await post_info_webhook(
            body="REST API Endpoint successfully started",
            source=WebhookSource.FASTAPI
        )
    except Exception as e:
        await post_error_webhook(
            title="Failed to start REST API Endpoint",
            body=str(e),
            source=WebhookSource.FASTAPI
        )


@app.on_event("shutdown")
async def shutdown():
    # Close the Neo4j driver connection
    driver.close()


###
# Wrapper for webhook reports

WEBHOOK_AVATAR_URL = "https://github.com/ryan-roche/gophermaps-data/blob/main/webhook-icons/gw-backend.png?raw=true"


class DiscordEmbedColor(Enum):
    """
    Semantic colors for webhook messages
    """
    ERROR = 0xc40000
    INFO = 0x0085ff


class WebhookSource(Enum):
    """
    What 'part' of the API produced a webhook message
    """
    FASTAPI = ("FastAPI", "https://github.com/ryan-roche/gophermaps-data/blob/main/webhook-icons/fastapi.png?raw=true")
    NEO4J = ("NEO4J", "https://github.com/ryan-roche/gophermaps-data/blob/main/webhook-icons/neo4j.png?raw=true")


class WebhookField(NamedTuple):
    title: str
    value: str
    inline: bool


class APICallSource(NamedTuple):
    name: str
    icon_url: str


async def post_info_webhook(body: str, source: WebhookSource):
    webhook = AsyncDiscordWebhook(url=DISCORD_WEBHOOK_URL, username="GopherMaps API", avatar_url=WEBHOOK_AVATAR_URL)

    # Build embed
    embed = DiscordEmbed(title="Notice", description=body, color=DiscordEmbedColor.INFO.value)
    embed.set_author(name=source.value[0], icon_url=source.value[1])
    embed.set_thumbnail(url="https://github.com/ryan-roche/gophermaps-data/blob/main/webhook-icons/info.png?raw=true")

    # Send to webhook
    webhook.add_embed(embed)
    await webhook.execute()


async def post_error_webhook(title: str,
                             body: str,
                             source: WebhookSource,
                             fields: List[WebhookField] = None,
                             caller: APICallSource = None):
    webhook = AsyncDiscordWebhook(url=DISCORD_WEBHOOK_URL, username="GopherMaps API", avatar_url=WEBHOOK_AVATAR_URL)

    # Build embed
    embed = DiscordEmbed(title=title, description=body, color=DiscordEmbedColor.ERROR.value)
    embed.set_author(name=source.value[0], icon_url=source.value[1])
    embed.set_thumbnail(url="https://github.com/ryan-roche/gophermaps-data/blob/main/webhook-icons/error.png?raw=true")

    for field in fields:
        embed.add_embed_field(name=field.title, value=field.value, inline=field.inline)

    if caller is not None:
        embed.set_footer(text=caller.name, icon_url=caller.icon_url)

    # Send to webhook
    webhook.add_embed(embed)
    await webhook.execute()


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


@app.get("/version", operation_id="apiVersion")
async def get_version() -> str:
    return app.version


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
) -> RouteResponseModel:
    """
    Get a route between two buildings, a list of the buildings along the route, and their associated thumbnails
    """
    with driver.session() as session:
        query = """
            MATCH (startNode {navID: $start}), (endNode {navID: $end}), path = shortestPath((startNode)-[*]-(endNode))
            WITH nodes(path) AS pathNodes, relationships(path) AS pathEdges
            UNWIND pathNodes AS node
            WITH pathNodes, pathEdges, COLLECT(DISTINCT node.buildingName) AS uniqueBuildingNames
            MATCH (buildingKey:BuildingKey)
            WHERE buildingKey.buildingName IN uniqueBuildingNames
            WITH pathNodes, pathEdges, COLLECT(buildingKey.buildingName) AS buildingNames, COLLECT(buildingKey.thumbnail) AS thumbnails
            RETURN pathNodes, pathEdges, buildingNames, thumbnails
            """
        parameters = {'start': start, 'end': end}
        result = session.run(query, parameters)

        record = result.single()

        if record is None:
            raise HTTPException(status_code=404, detail="Invalid Route")

        path_nodes: List[graph.Node] = record['pathNodes']
        path_edges: List[graph.Relationship] = record['pathEdges']
        building_names = record['buildingNames']
        thumbnails = record['thumbnails']

        # Create the pathNodes list
        parsed_nodes = [NavigationNodeModel(**node) for node in path_nodes]

        # Create the buildingThumbnails dictionary
        building_thumbnail_map = dict(zip(building_names, thumbnails))

        # Create the instructionsAvailable dictionary
        instructions_available = {}
        for i in range(len(path_edges)):
            start_node = path_nodes[i]
            end_node = path_nodes[i + 1]
            edge = path_edges[i]
            start_id = start_node['navID']
            end_id = end_node['navID']
            edge_key = f"{start_id}-{end_id}"
            instructions_available[edge_key] = edge['hasDetailedInstructions']

        return RouteResponseModel(pathNodes=parsed_nodes, buildingThumbnails=building_thumbnail_map,
                                  instructionsAvailable=instructions_available)

