from django.db import transaction
from rest_framework import serializers

from apps.menu.models import Dish
from apps.menu.serializers import DishSerializer

from .models import Order, OrderItem


def get_meal_period(hour):
    if 5 <= hour < 10:
        return "breakfast"
    elif 10 <= hour < 16:
        return "lunch"
    else:
        return "dinner"


class OrderItemSerializer(serializers.ModelSerializer):
    dish_detail = DishSerializer(source="dish", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "dish", "dish_detail", "quantity", "unit_price"]
        read_only_fields = ["unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "student_name",
            "student_no",
            "phone",
            "delivery_address",
            "pickup_time",
            "note",
            "status",
            "total_amount",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["total_amount", "created_at", "updated_at"]

    def validate(self, data):
        pickup_time = data["pickup_time"]
        pickup_date = pickup_time.date()
        meal_period = get_meal_period(pickup_time.hour)

        for item in data["items"]:
            dish = item["dish"]
            if dish.stock == 0:
                raise serializers.ValidationError(f"{dish.name} 已售罄。")
            if item["quantity"] < 1:
                raise serializers.ValidationError("菜品数量必须大于 0。")
            if dish.stock < item["quantity"]:
                raise serializers.ValidationError(f"{dish.name} 库存不足。")
            if dish.available_date != pickup_date:
                raise serializers.ValidationError(
                    f"{dish.name} 仅在 {dish.available_date} 供应，与预约日期不符。"
                )
            if dish.meal_period != meal_period:
                raise serializers.ValidationError(
                    f"{dish.name} 仅在 {dish.get_meal_period_display()} 供应，与预约时段不符。"
                )
        return data

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        order = Order.objects.create(**validated_data)
        pickup_date = order.pickup_time.date()
        meal_period = get_meal_period(order.pickup_time.hour)
        for item_data in items_data:
            dish = Dish.objects.select_for_update().get(id=item_data["dish"].id)
            quantity = item_data["quantity"]
            if dish.stock == 0:
                raise serializers.ValidationError(f"{dish.name} 已售罄。")
            if dish.stock < quantity:
                raise serializers.ValidationError(f"{dish.name} 库存不足。")
            if dish.available_date != pickup_date:
                raise serializers.ValidationError(
                    f"{dish.name} 仅在 {dish.available_date} 供应，与预约日期不符。"
                )
            if dish.meal_period != meal_period:
                raise serializers.ValidationError(
                    f"{dish.name} 仅在 {dish.get_meal_period_display()} 供应，与预约时段不符。"
                )
            dish.stock -= quantity
            dish.save(update_fields=["stock"])
            OrderItem.objects.create(order=order, dish=dish, quantity=quantity, unit_price=dish.price)
        order.recalculate_total()
        from apps.delivery.models import DeliveryTask

        DeliveryTask.objects.get_or_create(
            order=order,
            defaults={
                "status": "waiting",
                "estimated_arrival": order.pickup_time,
            },
        )
        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop("items", None)
        return super().update(instance, validated_data)
