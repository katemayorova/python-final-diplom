
import json

import pytest
from django.urls import reverse
from model_bakery import baker
from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from rest_framework.test import APIClient

from backend.models import User, Shop


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user_factory():
    def factory(**kwargs):
        return baker.make('backend.User', **kwargs)

    return factory


@pytest.fixture
def category_factory():
    def factory(**kwargs):
        return baker.make('backend.Category', **kwargs)

    return factory


@pytest.fixture
def shop_factory():
    def factory(**kwargs):
        return baker.make('backend.Shop', **kwargs)

    return factory


@pytest.fixture
def product_factory():
    def factory(**kwargs):
        return baker.make('backend.Product', **kwargs)

    return factory


@pytest.fixture
def product_info_factory():
    def factory(**kwargs):
        return baker.make('backend.ProductInfo', **kwargs)

    return factory


@pytest.mark.django_db
def test_category_view(api_client, category_factory, user_factory):
    categories_num = 10
    user = user_factory(is_active=True)
    categories = category_factory(_quantity=categories_num)
    url = reverse('backend:categories-list')
    api_client.force_authenticate(user=User.objects.get(email=user.email))

    resp = api_client.get(url)

    assert resp.status_code == HTTP_200_OK
    assert len(json.loads(resp.content)) == categories_num


@pytest.mark.django_db
def test_shop_view(api_client, shop_factory, user_factory):
    """проверяем просмотр категорий"""
    shops_num = 11
    user = user_factory(is_active=True)
    shops = shop_factory(_quantity=shops_num)
    url = reverse('backend:shops-list')
    api_client.force_authenticate(user=User.objects.get(email=user.email))

    resp = api_client.get(url)

    assert resp.status_code == HTTP_200_OK
    assert len(json.loads(resp.content)) == shops_num


@pytest.mark.django_db
def test_partner_state(api_client, user_factory, shop_factory):
    """проверяем получение и изменение статуса партнера, но не пользователя"""

    user = user_factory()
    partner = user_factory(type='shop')
    shop = shop_factory(user=partner)
    url = reverse('backend:partner-state')
    payload_off = {
        "state": "off"
    }

    shop_state_before = Shop.objects.filter(user_id=partner.id).first().state
    api_client.force_authenticate(user=User.objects.get(email=user.email))
    resp_user = api_client.get(url)
    api_client.force_authenticate(user=User.objects.get(email=partner.email))
    resp_partner_change = api_client.post(url, payload_off, format='json')
    api_client.force_authenticate(user=None)
    shop_state_after = Shop.objects.filter(user_id=partner.id).first().state

    assert resp_user.status_code == HTTP_403_FORBIDDEN
    assert json.loads(resp_user.content)['Error'] == 'Только для магазинов'
    assert shop_state_before is True
    assert resp_partner_change.status_code == HTTP_200_OK
    assert json.loads(resp_partner_change.content)['Status'] is True
    assert shop_state_after is False


@pytest.mark.django_db
def test_product_view(
        api_client,
        product_factory,
        category_factory,
        user_factory,
        shop_factory,
        product_info_factory
):
    """проверяем просмотр продукта"""
    user = user_factory(is_active=True)
    category = category_factory()
    shop = shop_factory()
    product = product_factory(category_id=category.id)
    product_info = product_info_factory(product_id=product.id, shop_id=shop.id)

    url = reverse('backend:products')
    api_client.force_authenticate(user=User.objects.get(email=user.email))

    resp = api_client.get(url)

    assert resp.status_code == HTTP_200_OK
    assert json.loads(resp.content)[0]['product']['name'] == product.name


@pytest.mark.django_db
def test_user_contacts(api_client, user_factory):   # не работает
    """проверяем добавление, просмотр и удаление контактов пользователем"""
    user = user_factory()
    url = reverse('backend:user-contact')
    api_client.force_authenticate(user=User.objects.get(email=user.email))

    payload_add = {
        "city": "Москва",
        "street": "Пушкина",
        "phone": "89206547377"
    }

    resp_add = api_client.post(url, payload_add, format='json')
    resp_view = api_client.get(url)

    contact_id = json.loads(resp_view.content)[0]['id']

    payload_delete = {
        "items": str(contact_id)
    }

    resp_delete = api_client.delete(url, payload_delete, format='json')

    resp_view_after_delete = api_client.get(url)

    assert resp_add.status_code == HTTP_200_OK
    assert json.loads(resp_add.content)['Status'] is True
    assert resp_view.status_code == HTTP_200_OK
    assert json.loads(resp_view.content)[0]['city'] == "Москва"
    assert json.loads(resp_view.content)[0]['street'] == "Пушкина"
    assert json.loads(resp_view.content)[0]['phone'] == "89206547377"
    assert resp_delete.status_code == HTTP_200_OK
    assert json.loads(resp_delete.content)['Status'] is True
    assert json.loads(resp_delete.content)['Objects deleted'] == 1
    assert resp_view_after_delete.status_code == HTTP_200_OK
    assert json.loads(resp_view_after_delete.content) == []


@pytest.mark.django_db
def test_user_details(api_client, user_factory):
    """проверяем получение авторизованным пользователем данных только своего аккаунта"""
    user = user_factory()
    another_user = user_factory()
    url = reverse('backend:user-details')
    resp_none = api_client.get(url)
    api_client.force_authenticate(user=User.objects.get(email=user.email))
    resp_user = api_client.get(url)
    api_client.force_authenticate(user=User.objects.get(email=another_user.email))
    resp_another_user = api_client.get(url)
    api_client.force_authenticate(user=None)

    assert resp_none.status_code == HTTP_403_FORBIDDEN
    assert resp_user.status_code == HTTP_200_OK
    assert json.loads(resp_user.content)['email'] == user.email
    assert resp_another_user.status_code == HTTP_200_OK
    assert json.loads(resp_another_user.content)['email'] == another_user.email


@pytest.mark.django_db
def test_user_details_change(api_client, user_factory):
    """проверяем изменение авторизованным пользователем данных аккаунта"""
    user = user_factory()
    name_to_change = 'Петров'
    url = reverse('backend:user-details')
    api_client.force_authenticate(user=User.objects.get(email=user.email))
    old_name = User.objects.get(email=user.email).last_name
    payload = {
        "last_name": name_to_change,
    }
    resp = api_client.post(url, payload, format='json')
    new_name = User.objects.get(email=user.email).last_name

    assert resp.status_code == HTTP_200_OK
    assert new_name == name_to_change
    assert new_name != old_name


@pytest.mark.django_db
def test_register_account_missed_fields(api_client):
    """проверяем регистрацию пользователя без обязательного поля"""
    url = reverse('backend:register-confirm')
    payload = {
        "last_name": "Иванов",
        "email": "ivanov0@gmail.com",
        "password": "123ABCabc%%",
        "company": "Midea",
        "position": "Директор"
    }
    resp = api_client.post(url, payload, format='json')

    assert resp.status_code == HTTP_200_OK
    assert json.loads(resp.content)['Status'] is False
    assert json.loads(resp.content)['Errors'] == 'Не указаны все необходимые параметры'


@pytest.mark.parametrize(
    ['password', 'expected_status'],
    (
            ('', False),
            ('fg88jj', False),
            ('123ABCabc%%', True)
    )
)
@pytest.mark.django_db
def test_register_account_passwords(api_client, password, expected_status):
    """проверяем регистрацию пользователя с разными паролями"""
    url = reverse('backend:user-register-confirm')
    payload = {
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": "ivanov0@gmail.com",
        "password": password,
        "company": "Midea",
        "position": "Директор"
    }
    resp = api_client.post(url, payload, format='json')
    assert resp.status_code == HTTP_200_OK
    assert json.loads(resp.content)['Status'] is expected_status


@pytest.mark.django_db
def test_user_login(api_client):
    """проверяем логин пользователя"""
    test_email = "ivanov0@gmail.com"
    test_password = "123ABCabc%%"

    url_register = reverse('backend:user-register-confirm')
    url_login = reverse('backend:user-login')

    payload_register = {
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": test_email,
        "password": test_password,
         "company": "Midea",
        "position": "Директор"
    }

    payload_login = {
        "email": test_email,
        "password": test_password
    }

    resp_register = api_client.post(url_register, payload_register, format='json')
    user = User.objects.get(email=test_email)
    user.is_active = True
    user.save()
    resp_login = api_client.post(url_login, payload_login, format='json')
    assert resp_register.status_code == HTTP_200_OK
    assert json.loads(resp_register.content)['Status'] is True
    assert resp_login.status_code == HTTP_200_OK
    assert json.loads(resp_login.content)['Status'] is True
    assert json.loads(resp_login.content)['Token'] is not None
