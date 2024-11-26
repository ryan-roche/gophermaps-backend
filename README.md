# gophermaps-backend

The backend stack for GopherMaps

[![Deploy to Amazon ECS](https://github.com/ryan-roche/gophermaps-backend/actions/workflows/ecs.yml/badge.svg?branch=main)](https://github.com/ryan-roche/gophermaps-backend/actions/workflows/ecs.yml)

---

Currently written in Python+FastAPI, with CI/CD in GitHubactions. Pushes to `main` trigger an automatic rebuild and deployment to Amazon ECS.

Our database is a Neo4j AuraDB Instance.
