from django.shortcuts import render
from rest_framework.generics import ListAPIView
from serializers import UserSerializer, OrderSerializer, CategorySerializer, ShopSerializer, \
    ProductInfoSerializer, OrderItemSerializer, ContactSerializer
from api.models import Order, OrderItem, Product, ConfirmEmailToken, Category, Shop, \
    ProductInfo, Parameter, ProductParameter, Contact


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer
