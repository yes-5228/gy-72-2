from decimal import Decimal

from rest_framework import serializers

from apps.menu.models import Dish
from apps.menu.serializers import DishSerializer


class NutritionAnalysisRequestSerializer(serializers.Serializer):
    dish_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )
    available_date = serializers.DateField(required=False)
    meal_period = serializers.CharField(required=False, max_length=20)


class NutritionAnalysisSerializer(serializers.Serializer):
    dishes = DishSerializer(many=True)
    totals = serializers.DictField()
    advice = serializers.ListField(child=serializers.CharField())


def analyze_dishes(dish_ids, available_date=None, meal_period=None):
    queryset = Dish.objects.filter(id__in=dish_ids, stock__gt=0).select_related("category")
    if available_date:
        queryset = queryset.filter(available_date=available_date)
    if meal_period:
        queryset = queryset.filter(meal_period=meal_period)
    dishes = list(queryset)
    available_ids = {dish.id for dish in dishes}
    unavailable_ids = [did for did in dish_ids if did not in available_ids]
    if unavailable_ids:
        raise serializers.ValidationError(
            f"部分菜品当前不可售（ID: {', '.join(map(str, unavailable_ids))}），请重新选择。"
        )
    totals = {
        "calories": sum(dish.calories for dish in dishes),
        "protein": sum(Decimal(dish.protein) for dish in dishes),
        "fat": sum(Decimal(dish.fat) for dish in dishes),
        "carbohydrate": sum(Decimal(dish.carbohydrate) for dish in dishes),
        "sodium": sum(dish.sodium for dish in dishes),
    }
    totals = {key: float(value) if isinstance(value, Decimal) else value for key, value in totals.items()}

    advice = []
    if totals["calories"] < 550:
        advice.append("本餐热量偏低，适合加一份主食或高蛋白菜品。")
    elif totals["calories"] > 900:
        advice.append("本餐热量偏高，建议减少油炸或高碳水菜品。")
    else:
        advice.append("本餐热量处于常规午/晚餐区间。")

    if totals["protein"] < 25:
        advice.append("蛋白质略少，可补充鸡蛋、鱼肉、豆制品等。")
    if totals["sodium"] > 1800:
        advice.append("钠含量偏高，建议搭配清淡汤品并减少调味酱。")
    if not advice:
        advice.append("营养搭配均衡。")

    return {"dishes": dishes, "totals": totals, "advice": advice}
