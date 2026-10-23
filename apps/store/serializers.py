from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apps.core.serializers import AllLanguagesModelSerializer
from apps.store.models import Ad, Category, Product, ProductImage, ProductReview


class AdSerializer(AllLanguagesModelSerializer):
    class Meta:
        model = Ad
        fields = [
            "id",
            "title",
            "subtitle",
            "image",
        ]


class CategorySerializer(AllLanguagesModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title", "image", "parent"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class ProductSerializer(AllLanguagesModelSerializer):
    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
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
            "images",
            "default_price",
            "compare_at_price",
            "discount_percentage",
            "stock_quantity",
            "reward_points",
            "is_newest",
            "is_best_seller",
        ]

    def validate(self, attrs):
        default_price = attrs.get(
            "default_price",
            self.instance.default_price if self.instance else 0,
        )
        compare_at_price = attrs.get(
            "compare_at_price",
            self.instance.compare_at_price if self.instance else None,
        )

        if compare_at_price is not None and compare_at_price <= default_price:
            raise serializers.ValidationError(
                {
                    "compare_at_price": _(
                        "Compare-at price must be greater than the default price."
                    )
                }
            )

        return attrs


class ProductReviewSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True,
    )

    class Meta:
        model = ProductReview
        fields = [
            "id",
            "product_id",
            "product",
            "rating",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "product",
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
