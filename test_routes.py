import pytest
from flask import Flask
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    """Prueba la ruta de inicio."""
    response = client.get("/")
    assert response.status_code == 200


def test_create_container(client):
    """Prueba la creación de un contenedor."""
    response = client.post(
        "/create_container",
        data={
            "name": "Contenedor de Prueba",
            "location": "Ubicación de Prueba",
            "items": "Item1, Item2",
            "pictures": [],  # Simular sin imágenes
        },
    )
    assert response.status_code == 302  # Redirección después de la creación


def test_container_detail(client):
    """Prueba la visualización de detalles de un contenedor."""
    # Primero, crea un contenedor para obtener su ID
    client.post(
        "/create_container",
        data={
            "name": "Contenedor de Prueba",
            "location": "Ubicación de Prueba",
            "items": "Item1, Item2",
            "pictures": [],
        },
    )
    response = client.get("/containers/1")  # Suponiendo que el ID es 1
    assert response.status_code == 200


def test_delete_container(client):
    """Prueba la eliminación de un contenedor."""
    # Primero, crea un contenedor para eliminar
    client.post(
        "/create_container",
        data={
            "name": "Contenedor de Prueba",
            "location": "Ubicación de Prueba",
            "items": "Item1, Item2",
            "pictures": [],
        },
    )
    response = client.post("/containers/1/delete")  # Suponiendo que el ID es 1
    assert response.status_code == 302  # Redirección después de la eliminación
