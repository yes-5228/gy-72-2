from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import NutritionAnalysisRequestSerializer, NutritionAnalysisSerializer, analyze_dishes


class NutritionAnalysisView(APIView):
    def post(self, request):
        request_serializer = NutritionAnalysisRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        validated = request_serializer.validated_data
        result = analyze_dishes(
            validated["dish_ids"],
            available_date=validated.get("available_date"),
            meal_period=validated.get("meal_period"),
            category=validated.get("category"),
            recommended=validated.get("recommended"),
            in_stock=validated.get("in_stock"),
        )
        response_serializer = NutritionAnalysisSerializer(result)
        return Response(response_serializer.data)
