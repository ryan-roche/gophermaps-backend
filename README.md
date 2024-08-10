# gophermaps-backend

The REST API backend for gophermaps.

Currently written in Python+FastAPI, but since serverless hosting is billed by runtime,
we may need to re-implement the API in something faster like Golang.

Our database is a Neo4j AuraDB Instance accessed through a serverless REST API endpoint (curerntly on Google Cloud Run)
