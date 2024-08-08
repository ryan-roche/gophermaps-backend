from main import app
from fastapi.testclient import TestClient


def main():
    client = TestClient(app)

    response = client.get("/areas")
    print(response.status_code)  # Output: 200
    print(response.json())       # Output: {'item_id': 1, 'name': 'Item 1'}

    print()

    response = client.get("/buildings/TestBuildings")
    print(response.status_code)
    print(response.json())

    print()

    response = client.get("/destinations/Test Building 3")
    print(response.status_code)
    print(response.json())

    client.close()


if __name__ == "__main__":
    main()
