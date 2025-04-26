# В общем, слегка плохо вижу тут отступы (точнее, они как-то немного странно делаются), 
# поэтому просто вставлю из VS Code сразу весь блок кода, а не буду выборочно редактировать
import pytest

@pytest.mark.asyncio
async def test_create_seller(async_client):
    payload = {
        "first_name": "Владимир",
        "last_name": "Смирнов",
        "e_mail": "smirnovve2003@gmail.com",
        "password": "1972"
    }
    response = await async_client.post("/api/v1/seller/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["first_name"] == payload["first_name"]
    assert "password" not in data

@pytest.mark.asyncio
async def test_get_all_sellers(async_client):
    response = await async_client.get("/api/v1/seller/")
    assert response.status_code == 200
    sellers = response.json()
    assert isinstance(sellers, list)
    if sellers:
        assert "password" not in sellers[0]  

@pytest.mark.asyncio
async def test_get_seller(async_client):
    payload = {
        "first_name": "Иван",
        "last_name": "Самарин",
        "e_mail": "samarin2003@gmail.com",
        "password": "secret"
    }
    create_resp = await async_client.post("/api/v1/seller/", json=payload)
    seller_id = create_resp.json()["id"]
    
    response = await async_client.get(f"/api/v1/seller/{seller_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == seller_id
    assert "books" in data 
    assert "password" not in data  

@pytest.mark.asyncio
async def test_update_seller(async_client):
    payload = {
        "first_name": "Аль",
        "last_name": "Пачино",
        "e_mail": "pacinogodfather1972@gmail.com",
        "password": "kopolla"
    }
    create_resp = await async_client.post("/api/v1/seller/", json=payload)
    seller_id = create_resp.json()["id"]
        
    update_payload = {
        "first_name": "АльUpdated",
        "last_name": "ПачиноUpdated",
        "e_mail": "pacinogodfather1972_updated@gmail.com",
    }
    response = await async_client.put(f"/api/v1/seller/{seller_id}", json=update_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "АльUpdated"
    assert data["last_name"] == "ПачиноUpdated"
    assert data["e_mail"] == "pacinogodfather1972_updated@gmail.com"
    assert "password" not in data 

@pytest.mark.asyncio
async def test_delete_seller(async_client):
    payload = {
        "first_name": "Алексей",
        "last_name": "Алексеев",
        "e_mail": "alekseev@gmail.com",
        "password": "secret"
    }
    create_resp = await async_client.post("/api/v1/seller/", json=payload)
    seller_id = create_resp.json()["id"]
        
    # Удаление продавца
    del_resp = await async_client.delete(f"/api/v1/seller/{seller_id}")
    assert del_resp.status_code == 204

    # Проверка, что продавец был удален
    get_resp = await async_client.get(f"/api/v1/seller/{seller_id}")
    assert get_resp.status_code == 404  

@pytest.mark.asyncio
async def test_create_seller_with_invalid_data(async_client):
    payload = {
        "first_name": "",
        "last_name": "",
        "e_mail": "invalid-email",
        "password": ""
    }
    response = await async_client.post("/api/v1/seller/", json=payload)
    assert response.status_code == 422 
    data = response.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_update_seller_with_invalid_data(async_client):
    payload = {
        "first_name": "Иван",
        "last_name": "Иванов",
        "e_mail": "ivanov@example.com",
        "password": "password"
    }
    create_resp = await async_client.post("/api/v1/seller/", json=payload)
    seller_id = create_resp.json()["id"]

    update_payload = {
        "first_name": "",
        "last_name": "",
        "e_mail": "invalid-email",
    }
    response = await async_client.put(f"/api/v1/seller/{seller_id}", json=update_payload)
    assert response.status_code == 422 
    data = response.json()
    assert "detail" in data
