from rest_framework import serializers

from apps.store.models import Ad, Category, Product


class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = [
            "id",
            "title",
            "subtitle",
            "image",
        ]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "image", "parent"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        write_only=True,
    )

    class Meta:
        model = Product
        fields = [
            "id",
            "category_id",
            "category",
            "title",
            "description",
            "image",
            "default_price",
            "quantity",
            "points",
            "is_newest",
            "is_best_seller",
        ]
