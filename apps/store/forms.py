from __future__ import annotations

from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _
from unfold.widgets import (
    UnfoldAdminDecimalFieldWidget,
    UnfoldAdminImageFieldWidget,
    UnfoldAdminIntegerFieldWidget,
    UnfoldAdminSelectWidget,
    UnfoldAdminTextareaWidget,
    UnfoldAdminTextInputWidget,
    UnfoldBooleanSwitchWidget,
)

from apps.store.models import Category, Product


class ProductAdminForm(forms.ModelForm):
    title_en = forms.CharField(
        label=_("Product name"),
        max_length=255,
        widget=UnfoldAdminTextInputWidget(
            attrs={
                "dir": "ltr",
                "lang": "en",
                "placeholder": "Enter the product name in English",
                "autocomplete": "off",
            }
        ),
    )

    title_ar = forms.CharField(
        label=_("اسم المنتج"),
        max_length=255,
        widget=UnfoldAdminTextInputWidget(
            attrs={
                "dir": "rtl",
                "lang": "ar",
                "placeholder": "أدخل اسم المنتج باللغة العربية",
                "autocomplete": "off",
            }
        ),
    )

    description_en = forms.CharField(
        label=_("Full description"),
        max_length=2000,
        widget=UnfoldAdminTextareaWidget(
            attrs={
                "dir": "ltr",
                "lang": "en",
                "rows": 8,
                "placeholder": (
                    "Describe the product, its benefits, " "features, and usage."
                ),
            }
        ),
    )

    description_ar = forms.CharField(
        label=_("الوصف الكامل"),
        max_length=2000,
        widget=UnfoldAdminTextareaWidget(
            attrs={
                "dir": "rtl",
                "lang": "ar",
                "rows": 8,
                "placeholder": ("اكتب وصف المنتج ومميزاته وفوائده " "وطريقة استخدامه"),
            }
        ),
    )

    category: forms.ModelChoiceField[Category] = forms.ModelChoiceField(
        label=_("Category"),
        queryset=Category.objects.select_related(
            "branch",
            "branch__brand",
        ).all(),
        empty_label=_("Select a category"),
        widget=UnfoldAdminSelectWidget(),
    )

    image = forms.ImageField(
        label=_("Primary product image"),
        required=False,
        help_text=_("Use a square JPG, PNG, or WebP image " "for the best result."),
        widget=UnfoldAdminImageFieldWidget(),
    )

    default_price = forms.DecimalField(
        label=_("Selling price"),
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=UnfoldAdminDecimalFieldWidget(
            attrs={
                "min": "0",
                "step": "0.01",
                "inputmode": "decimal",
            }
        ),
    )

    compare_at_price = forms.DecimalField(
        label=_("Compare-at price"),
        required=False,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        help_text=_("Optional. It must be greater than the selling price."),
        widget=UnfoldAdminDecimalFieldWidget(
            attrs={
                "min": "0",
                "step": "0.01",
                "inputmode": "decimal",
            }
        ),
    )

    stock_quantity = forms.IntegerField(
        label=_("Available quantity"),
        min_value=0,
        widget=UnfoldAdminIntegerFieldWidget(
            attrs={
                "min": "0",
                "step": "1",
                "inputmode": "numeric",
            }
        ),
    )

    reward_points = forms.IntegerField(
        label=_("Reward points"),
        min_value=0,
        widget=UnfoldAdminIntegerFieldWidget(
            attrs={
                "min": "0",
                "step": "1",
                "inputmode": "numeric",
            }
        ),
    )

    is_newest = forms.BooleanField(
        label=_("Show as new"),
        required=False,
        widget=UnfoldBooleanSwitchWidget(),
    )

    is_best_seller = forms.BooleanField(
        label=_("Show as best seller"),
        required=False,
        widget=UnfoldBooleanSwitchWidget(),
    )

    class Meta:
        model = Product

        fields = (
            "title_en",
            "title_ar",
            "description_en",
            "description_ar",
            "category",
            "image",
            "default_price",
            "compare_at_price",
            "stock_quantity",
            "reward_points",
            "is_newest",
            "is_best_seller",
        )

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean() or {}

        default_price = cleaned_data.get("default_price")
        compare_at_price = cleaned_data.get("compare_at_price")

        if (
            default_price is not None
            and compare_at_price is not None
            and compare_at_price <= default_price
        ):
            self.add_error(
                "compare_at_price",
                _("Compare-at price must be greater " "than the selling price."),
            )

        return cleaned_data
