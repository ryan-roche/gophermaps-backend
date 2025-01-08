# gophermaps-backend

The backend stack for GopherMaps

---

Currently written in Python+FastAPI with CI/CD in GitHub Actions. Pushes to relevant files in `prod` trigger an automatic rebuild and deployment to Amazon EC2 via CodeDeploy and GitHub Actions.

Our database is a Neo4j AuraDB Instance.
