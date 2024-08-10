> [!NOTE]
> Currently in the process of migrating to Cloud hosting in preparation for the 2024 Fall Semester

### TODOs
- [ ] Choose between AWS Lambda and Azure Functions for serverless API hosting
- [ ] Host database on N4j

# gophermaps-backend

The REST API backend for gophermaps.

Currently implemented in Python+FastAPI, but since serverless hosting is billed by runtime,
we may need to re-implement the API in something faster like Golang.
