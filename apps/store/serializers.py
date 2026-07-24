from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.store.models import Ad, Category, Product, ProductReview


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
            "stock_quantity",
            "reward_points",
            "is_newest",
            "is_best_seller",
        ]


class ProductReviewSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "product_id",
            "product",
            "user_id",
            "user_full_name",
            "rating",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "product",
            "user_id",
            "user_full_name",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        if self.instance and "product" in attrs:
            raise serializers.ValidationError(
                {"product_id": _("Product cannot be changed.")}
            )

        request = self.context.get("request")
        user = getattr(request, "user", None)
        product = attrs.get("product")

        if (
            request
            and request.method == "POST"
            and user
            and product
            and ProductReview.objects.filter(product=product, user=user).exists()
        ):
            raise serializers.ValidationError(
                {"product_id": _("You already reviewed this product.")}
            )

        return attrs
