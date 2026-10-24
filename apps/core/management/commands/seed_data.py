import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.authentication.models import GuestUser
from apps.store.models import (
    Ad,
    Brand,
    Branch,
    Category,
    Product,
    ProductImage,
    ProductReview,
)


class Command(BaseCommand):
    help = "Create or update bilingual development seed data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="WaslaDemo123!",
            help="Password assigned to the seeded demo accounts.",
        )

    def handle(self, *args, **options):
        environment = os.environ.get("ENV", "local").strip().lower()
        if environment not in {"local", "dev", "development"}:
            raise CommandError(
                "seed_data can run only in local or development environments."
            )

        password = options["password"]
        if not password:
            raise CommandError("The seed account password cannot be empty.")

        with transaction.atomic():
            users = self._seed_users(password)
            self._seed_guest_user()
            self._seed_ads()
            branch = self._seed_catalog_owners()
            categories = self._seed_categories(branch)
            products = self._seed_products(categories)
            self._seed_product_images(products)
            self._seed_product_reviews(products, users)

        self.stdout.write(
            self.style.SUCCESS(
                "Seed data ready: 3 users, 1 guest, 2 ads, 1 brand, 1 branch, "
                "6 categories, 6 products, 12 product images, and 6 product reviews."
            )
        )
        self.stdout.write("Admin phone: +201000000001")
        self.stdout.write("Customer phones: +201000000002, +201000000003")
        self.stdout.write(f"Demo password: {password}")

    def _seed_users(self, password):
        user_model = get_user_model()
        user_data = (
            {
                "phone": "+201000000001",
                "email": "admin@wasla.local",
                "full_name": "Wasla Admin",
                "reward_points": 500,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "phone": "+201000000002",
                "email": "nour@wasla.local",
                "full_name": "Nour Hassan",
                "reward_points": 120,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "phone": "+201000000003",
                "email": "salma@wasla.local",
                "full_name": "Salma Ahmed",
                "reward_points": 75,
                "is_staff": False,
                "is_superuser": False,
            },
        )
        users = {}

        for values in user_data:
            phone = values["phone"]
            defaults = {**values, "is_active": True}
            defaults.pop("phone")
            user, _ = user_model.objects.update_or_create(
                phone=phone,
                defaults=defaults,
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            users[phone] = user

        return users

    def _seed_guest_user(self):
        GuestUser.objects.get_or_create(session_key="seed-guest-session")

    def _seed_ads(self):
        ads = (
            (
                "Glow Every Day",
                "تألقي كل يوم",
                "Discover skincare essentials selected for your daily routine.",
                "اكتشفي أساسيات العناية بالبشرة المختارة لروتينك اليومي.",
            ),
            (
                "Beauty Rewards",
                "مكافآت الجمال",
                "Earn points with every order and save on your next purchase.",
                "اجمعي النقاط مع كل طلب ووفري في عملية الشراء التالية.",
            ),
        )

        for title_en, title_ar, subtitle_en, subtitle_ar in ads:
            Ad.objects.update_or_create(
                title_en=title_en,
                defaults={
                    "title": title_en,
                    "title_ar": title_ar,
                    "subtitle": subtitle_en,
                    "subtitle_en": subtitle_en,
                    "subtitle_ar": subtitle_ar,
                    "image": "default.jpeg",
                },
            )

    def _seed_catalog_owners(self):
        brand, _ = Brand.objects.update_or_create(
            title_en="Wasla",
            defaults={
                "title": "Wasla",
                "title_ar": "وصلة",
                "image": "default.jpeg",
            },
        )
        branch, _ = Branch.objects.update_or_create(
            brand=brand,
            title_en="Main Branch",
            defaults={
                "title": "Main Branch",
                "title_ar": "الفرع الرئيسي",
                "image": "default.jpeg",
            },
        )
        return branch

    def _seed_categories(self, branch):
        categories = {}
        roots = (
            ("skincare", "Skincare", "العناية بالبشرة"),
            ("haircare", "Hair Care", "العناية بالشعر"),
            ("makeup", "Makeup", "المكياج"),
        )
        children = (
            ("face", "Face Care", "العناية بالوجه", "skincare"),
            ("lips", "Lips", "الشفاه", "makeup"),
            ("eyes", "Eyes", "العيون", "makeup"),
        )

        for key, title_en, title_ar in roots:
            category, _ = Category.objects.update_or_create(
                branch=branch,
                title_en=title_en,
                defaults={
                    "title": title_en,
                    "title_ar": title_ar,
                    "parent": None,
                    "image": "default.jpeg",
                },
            )
            categories[key] = category

        for key, title_en, title_ar, parent_key in children:
            category, _ = Category.objects.update_or_create(
                branch=branch,
                title_en=title_en,
                defaults={
                    "title": title_en,
                    "title_ar": title_ar,
                    "parent": categories[parent_key],
                    "image": "default.jpeg",
                },
            )
            categories[key] = category

        return categories

    def _seed_products(self, categories):
        product_data = (
            (
                "Vitamin C Glow Serum",
                "سيروم فيتامين سي للإشراق",
                "A lightweight brightening serum for an even-looking complexion.",
                "سيروم خفيف للإشراق يساعد على توحيد مظهر البشرة.",
                "face",
                "699.00",
                "799.00",
                30,
                70,
                True,
                True,
            ),
            (
                "Hydrating Face Cleanser",
                "غسول وجه مرطب",
                "A gentle daily cleanser that removes impurities without dryness.",
                "غسول يومي لطيف يزيل الشوائب دون التسبب في الجفاف.",
                "face",
                "349.00",
                None,
                45,
                35,
                False,
                True,
            ),
            (
                "Daily Sunscreen SPF 50",
                "واقي شمس يومي بعامل حماية 50",
                "Broad-spectrum daily protection with a comfortable finish.",
                "حماية يومية واسعة الطيف بلمسة نهائية مريحة.",
                "skincare",
                "525.00",
                "600.00",
                25,
                55,
                True,
                False,
            ),
            (
                "Argan Nourishing Hair Oil",
                "زيت الأرجان المغذي للشعر",
                "A smoothing hair oil that adds shine and helps reduce frizz.",
                "زيت للشعر يمنح النعومة واللمعان ويساعد على تقليل الهيشان.",
                "haircare",
                "450.00",
                None,
                20,
                45,
                False,
                False,
            ),
            (
                "Velvet Matte Lipstick",
                "أحمر شفاه مخملي مطفي",
                "Rich color with a soft matte finish and comfortable wear.",
                "لون غني بلمسة مطفية ناعمة ومريحة طوال اليوم.",
                "lips",
                "299.00",
                "350.00",
                60,
                30,
                True,
                True,
            ),
            (
                "Volume Lift Mascara",
                "ماسكارا لرفع وتكثيف الرموش",
                "Buildable mascara for lifted lashes and defined volume.",
                "ماسكارا قابلة للتكثيف لرفع الرموش ومنحها حجمًا محددًا.",
                "eyes",
                "375.00",
                None,
                40,
                40,
                False,
                True,
            ),
        )
        products = {}

        for (
            title_en,
            title_ar,
            description_en,
            description_ar,
            category_key,
            default_price,
            compare_at_price,
            stock_quantity,
            reward_points,
            is_newest,
            is_best_seller,
        ) in product_data:
            product, _ = Product.objects.update_or_create(
                title_en=title_en,
                defaults={
                    "title": title_en,
                    "title_ar": title_ar,
                    "description": description_en,
                    "description_en": description_en,
                    "description_ar": description_ar,
                    "category": categories[category_key],
                    "image": "default.jpeg",
                    "default_price": Decimal(default_price),
                    "compare_at_price": (
                        Decimal(compare_at_price) if compare_at_price else None
                    ),
                    "stock_quantity": stock_quantity,
                    "reward_points": reward_points,
                    "is_newest": is_newest,
                    "is_best_seller": is_best_seller,
                },
            )
            products[title_en] = product

        return products

    def _seed_product_images(self, products):
        for product in products.values():
            existing_count = ProductImage.objects.filter(
                product=product,
                image="default.jpeg",
            ).count()
            for _ in range(max(0, 2 - existing_count)):
                ProductImage.objects.create(product=product, image="default.jpeg")

    def _seed_product_reviews(self, products, users):
        customers = (
            users["+201000000002"],
            users["+201000000003"],
        )
        review_data = (
            ("Vitamin C Glow Serum", 5, "Visible glow and a light texture."),
            ("Hydrating Face Cleanser", 4, "Gentle enough for everyday use."),
            ("Daily Sunscreen SPF 50", 5, "Comfortable finish without heaviness."),
            ("Argan Nourishing Hair Oil", 4, "Leaves my hair smooth and shiny."),
            ("Velvet Matte Lipstick", 5, "Rich color and comfortable wear."),
            ("Volume Lift Mascara", 4, "Good definition without clumping."),
        )

        for index, (product_title, rating, description) in enumerate(review_data):
            ProductReview.objects.update_or_create(
                product=products[product_title],
                user=customers[index % len(customers)],
                defaults={
                    "rating": rating,
                    "description": description,
                },
            )
