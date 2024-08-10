import random
from django.db import transaction
from django.db.models import Avg, Q
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# Third party imports
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from phonenumber_field.serializerfields import PhoneNumberField

#local imports
from core.models import Addresses, Books, BooksReview, CustomUser, Materials, MaterialsReview, MobileUsers, ProReview, Professionals, Referrals, generate_referral_code
from mobile_app.models import Cart, Favorite, Order, OrderItem


# Create your serializers here

# USER MANAGEMENT SERIALIZERS
class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ['first_name', 'last_name', 'email', 'phone_no', 'fcm_token', 'referral_code']
        extra_kwargs = {
            'phone_no': {'required': True, 'allow_blank': False, 'allow_null': False},
            'fcm_token': {'required': True, 'allow_blank': False, 'allow_null': False},
            'referral_code': {'required': False, 'allow_blank': True, 'allow_null': True, 'read_only': True},
        }

    def validate(self, attrs):
        referral_code = self.context.get("referral_code")
        print(referral_code)

        errors = {}

        # Validate the referral code
        if referral_code:
            try:
                referrer = MobileUsers.objects.get(referral_code=referral_code)
                attrs['referrer'] = referrer
            except MobileUsers.DoesNotExist:
                errors.setdefault("referral_code", []).append("Code does not exist")

        if errors:
            raise serializers.ValidationError(errors)    

        return attrs


    def create(self, validated_data):
        referrer = validated_data.pop('referrer', None)
        
        # if any operation fails, the entire transaction will be rolled back.
        with transaction.atomic():
            # Creating a custom user
            custom_user = CustomUser()
            custom_user.save()

            # Add the user to USER group
            group, _ = Group.objects.get_or_create(name='USER')
            custom_user.groups.add(group)

            #  Creating a Mobile user
            mobile_user = self.Meta.model(**validated_data)
            mobile_user.user = custom_user
            mobile_user.referral_code = generate_referral_code()
            mobile_user.save()

            message = "Mobile user registerd successfully!"

            # Creating the referral
            if referrer:
                referral=Referrals.objects.create(referrer=referrer, referred=mobile_user)

                # Add one new referral to referrer
                referrer.total_referrels += 1
                referrer.save()

                message = "Mobile user with referrer created successfully!"

        return mobile_user, message
    

class GetOTPSerializer(serializers.Serializer):
    phone_no = PhoneNumberField(region="IN")

    def validate(self, attrs):
        phone_no = attrs.get("phone_no")

        try:
            user = MobileUsers.objects.get(phone_no=phone_no)
        except MobileUsers.DoesNotExist:
            raise serializers.ValidationError({"phone_no": "user not found"})
        
        attrs["user"] = user
        
        return attrs

    def save(self):
        otp = random.randint(1000, 9999)

        print(self.validated_data)
        user = self.validated_data["user"]
        user.otp = otp
        user.save()

        return user


class OTPVerficationSerializer(serializers.Serializer):
    phone_no = PhoneNumberField(region="IN")
    otp = serializers.IntegerField()

    def validate(self, data):
        phone_no = data["phone_no"]
        otp = data["otp"]

        if not(1000 <= otp <= 9999):
            raise serializers.ValidationError({"otp": "OTP must be exactly 4 digits"})
        
        try:
            user = MobileUsers.objects.get(phone_no=phone_no)
        except MobileUsers.DoesNotExist:
            raise serializers.ValidationError({"phone_no": "User not found"})
        
        # Change otp to string becouse it is mentioned as CharField in model
        if not user.otp or user.otp != str(otp):
            raise serializers.ValidationError({"otp": "Invalid otp"})
        
        data["user"] = user
        data["custom_user"] =user.user

        return data
    
    def save(self):
        user = self.validated_data["user"]
        custom_user = self.validated_data["custom_user"]

        # Change the otp to none
        user.otp = None
        user.save()

        # Generate tokens (using Simple JWT library)
        refresh = RefreshToken.for_user(custom_user)
        access = refresh.access_token 

        tokens = {
            'access': str(access),
            'refresh': str(refresh),
            'image': user.image if user.image else "",
            'name': user.first_name
        }

        return tokens
    

class UserLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def save(self):
        # Attempt to blacklist the refresh token to log out the user
        try:
            RefreshToken(self.validated_data['refresh']).blacklist()
        except Exception as e:
            raise serializers.ValidationError({"refresh": str(e)})
        
        return


class HomeSearchSerializer(serializers.Serializer):
    search = serializers.CharField(max_length=150)

    def to_representation(self, instance):
        search = instance["search"]
        search = search.strip()
        request = self.context.get("request")

        representation = {}

        professioanls = Professionals.objects.filter(
            Q(name__icontains=search) | 
            Q(location__icontains=search) | 
            Q(expertise__icontains=search)
        )

        products = Materials.objects.filter(
            Q(name__icontains=search) | 
            Q(type__icontains=search) | 
            Q(supplier_name__icontains=search) | 
            Q(title__icontains=search)
        )

        professioanls = ProfessionalsListSerializer(professioanls, many=True, context={"request": request})
        products = ListMaterialsSerializer(products, many=True, context={"request": request})

        representation["professionals"] = professioanls.data
        representation["products"] = products.data

        return representation


class EditUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ["first_name", "email", "phone_no", "image"]


class TopBrandsListSerializer(serializers.Serializer):
    supplier_name = serializers.CharField()
    average_rating = serializers.FloatField()
    material_count = serializers.IntegerField()


# PROFESSIONALS SERIALIZERS *******
class ProfessionalsListSerializer(serializers.ModelSerializer):
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Professionals
        fields = ["id", "name", "location", "banner", "expertise", "phone_no", "is_liked"]
    
    def get_is_liked(self, obj):
        request = self.context["request"]
        user = MobileUsers.objects.get(user=request.user)
        
        return user.favorites.filter(type="professional", item_id=obj.id).exists()


class ProReviewSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.related_user.first_name', read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = ProReview
        fields = ['created_by_name', 'rating', 'review', 'role']

    def get_role(self, obj):
        return 'admin' if obj.created_by.is_superuser else 'client'


class ProfessionalsDetailSerializer(serializers.ModelSerializer):
    portfolios =  serializers.SerializerMethodField()
    reviews = ProReviewSerializer(many=True, read_only=True, source='review_professional')
    average_ratings = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Professionals
        fields = [
            'name', 'phone_no', 'email', 'expertise', 'location', 'about', 'experiance', 
            'banner', 'website', 'created_on', 'last_edited', 'portfolios', 'reviews', 
            'average_ratings', "is_liked"
        ]

    def get_average_ratings(self, obj):
        return obj.average_ratings
    
    def get_portfolios(self, obj):
        request = self.context.get('request')
        portfolios = obj.porfolios.all()

        grouped_portfolios = {}
        for portfolio in portfolios:
            if portfolio.title not in grouped_portfolios:
                grouped_portfolios[portfolio.title] = []
            grouped_portfolios[portfolio.title].append({
                "id": portfolio.id,
                "image": request.build_absolute_uri(portfolio.image.url)
            })

        formatted_portfolios = [
            {
                "title": title,
                "images": images
            }
            for title, images in grouped_portfolios.items()
        ]

        return formatted_portfolios
    
    def get_is_liked(self, obj):
        request = self.context["request"]
        user = MobileUsers.objects.get(user=request.user)
        
        return user.favorites.filter(type="professional", item_id=obj.id).exists()
    

class AddProfessionalsReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProReview
        fields = ["rating", "review", "created_by", "professional"]


# Materials Serializers *******
class ListMaterialsSerializer(serializers.ModelSerializer):
    is_liked = serializers.SerializerMethodField()
    average_ratings = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Materials
        fields = [
            "id", "name", "supplier_name", "availability", "image", "title", "is_liked", 
            "price", "discount_percentage", "discounted_price", "average_ratings" 
        ]
    
    def get_is_liked(self, obj):
        request = self.context["request"]
        user = MobileUsers.objects.get(user=request.user)
        
        return user.favorites.filter(type="material", item_id=obj.id).exists()
    
    def get_average_ratings(self, obj):
        return obj.average_ratings
    
    def get_discounted_price(self, obj):
        return obj.discounted_price
    

class MaterialsReviewsSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.first_name")
    role = serializers.CharField(default="client")
    class Meta:
        model = MaterialsReview
        fields = ["created_by_name", "rating", "review", "role"]
    

class MaterialsDetailedRetrieveSerializer(serializers.ModelSerializer):
    is_liked = serializers.SerializerMethodField()
    reviews = MaterialsReviewsSerializer(many=True, read_only=True)
    average_ratings = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Materials
        fields = [
            "name", "type", "supplier_name", "supplier_phone_no", "price", 
            "discount_percentage", "discounted_price", "title", "availability", 
            "image", "description", "overview", "additional_details", "reviews",
            "average_ratings", "is_liked"
        ]

    def get_average_ratings(self, obj):
        return obj.average_ratings
    
    def get_discounted_price(self, obj):
        return obj.discounted_price
    
    def get_is_liked(self, obj):
        request = self.context["request"]
        user = MobileUsers.objects.get(user=request.user)
        
        return user.favorites.filter(type="material", item_id=obj.id).exists()


class AddMaterialsReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialsReview
        fields = ["rating", "review", "created_by", "material"]


#BOOKS SERIALIZERS *******
class BooksListSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Books
        fields = [
            "id",
            "image", 
            "name", 
            "price", 
            "availability", 
            "description", 
            "additional_details", 
            "discount_percentage", 
            "discounted_price"
        ]

    def get_discounted_price(self, obj):
        if obj.discount_percentage == 0 or not obj.discount_percentage:
            return obj.price
        
        return obj.price - (obj.discount_percentage * obj.price)/100
    

class BooksReviewsSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.first_name")
    role = serializers.CharField(default="client")
    class Meta:
        model = BooksReview
        fields = ["created_by_name", "rating", "review", "role"]


class BooksDetaledRetrieveSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()
    reviews = BooksReviewsSerializer(many=True, read_only=True)
    average_ratings = serializers.SerializerMethodField()
    related_books = serializers.SerializerMethodField()

    class Meta:
        model = Books
        fields = [
            "name", 
            "price", 
            "discount_percentage",
            "discounted_price",
            "description", 
            "additional_details", 
            "image", 
            "availability", 
            "created_on", 
            "last_edited", 
            "reviews", 
            "average_ratings",
            "related_books"
        ]

    def get_average_ratings(self, obj):
        average_rating = obj.reviews.aggregate(Avg('rating'))['rating__avg']

        return average_rating if average_rating is not None else 0
    
    def get_discounted_price(self, obj):
        if obj.discount_percentage == 0 or not obj.discount_percentage:
            return obj.price
        
        return obj.price - (obj.discount_percentage * obj.price)/100
    
    def get_related_books(self, obj):
        related_books = Books.objects.filter(
            Q(name__icontains=obj.name) | 
            Q(description__icontains=obj.description) |
            Q(additional_details__icontains=obj.additional_details)
        ).exclude(id=obj.id)[:15]

        serializer = BooksListSerializer(related_books, many=True, context=self.context)

        return serializer.data
    
class AddBooksReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = BooksReview
        fields = ["rating", "review", "created_by", "book"]


# ADDRESS MODULE SERIALIZERS *******
class AddressCreateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addresses
        fields = "__all__"

        extra_kwargs = {
            'type': {'required': True}
        }


class AddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addresses
        fields = [
            "type",
            "name", 
            "phone_no", 
            "city", 
            "state", 
            "street", 
            "flat_no",
            "landmark",
            "is_default",
        ]

        extra_kwargs = {
            'type': {'required': True}
        }


# FAVORITE MODULE SERIALIZERS *******
class AddFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['type', 'item_id', 'user']

    def validate(self, data):
        item_type = data.get('type')
        item_id = data.get('item_id')

        errors = {}
        if item_type == 'professional':
            if not Professionals.objects.filter(id=item_id).exists():
                errors.setdefault("item_id", []).append("Professional does not exist.")

        elif item_type == 'book':
            if not Books.objects.filter(id=item_id).exists():
                errors.setdefault("item_id", []).append("Book does not exist.")
            
        elif item_type == 'material':
            if not Materials.objects.filter(id=item_id).exists():
                errors.setdefault("item_id", []).append("Material does not exist.")
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return data
    

class RemoveFavoriteSeializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['type', 'item_id']


# CART MODULE SERIALIZERS *******
class AddCartSerializer(serializers.Serializer):
    TYPE_CHOICES = [('book', 'Book'), ('material', 'Material')]

    type = serializers.ChoiceField(choices=TYPE_CHOICES)
    item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(required=False)

    def validate(self, attrs):
        quantity = attrs.get('quantity')
        item_id = attrs.get('item_id')

        errors = {}
        if quantity is not None and quantity < 1:
            errors.setdefault("quantity", []).append("Must be positive integer.")
        
        if item_id <= 0:
            errors.setdefault("item_id", []).append("Must be positive integer.")

        if errors:
            raise serializers.ValidationError(errors)       
        
        return attrs
    

class UpdateCartQuantitySerializer(serializers.Serializer):
    TYPE_CHOICES = [('book', 'Book'), ('material', 'Material')]

    type = serializers.ChoiceField(choices=TYPE_CHOICES)
    item_id = serializers.IntegerField()
    quantity = serializers.IntegerField()

    def validate(self, attrs):
        quantity = attrs.get('quantity')
        item_id = attrs.get('item_id')

        errors = {}
        if quantity < 0:
            errors.setdefault("quantity", []).append("Must be positive integer.")
        
        if item_id <= 0:
            errors.setdefault("item_id", []).append("Must be positive integer.")

        if errors:
            raise serializers.ValidationError(errors)       
        
        return attrs
    
class CartItemSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    average_ratings = serializers.SerializerMethodField()
    availability = serializers.SerializerMethodField()
    item_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'quantity', 'created_on', 'type', 'item_id', 'name', 'image', 
            'price', 'discount_percentage', 'discounted_price', 'average_ratings', 
            'availability'
        ]

    def get_type(self, obj):
        if obj.book:
            return 'book'
        elif obj.material:
            return 'material'
        return None
    
    def get_item_id(seld, obj):
        if obj.book:
            return obj.book.id
        elif obj.material:
            return obj.material.id
        return None
    
    def get_name(seld, obj):
        if obj.book:
            return obj.book.name
        elif obj.material:
            return obj.material.name
        return None

    def get_image(self, obj):
        request = self.context["request"]
        if obj.book:
            return request.build_absolute_uri(obj.book.image.url)
        elif obj.material:
            return request.build_absolute_uri(obj.material.image.url)
        return None

    def get_price(self, obj):
        if obj.book:
            return obj.book.price
        elif obj.material:
            return obj.material.price
        return None

    def get_discount_percentage(self, obj):
        if obj.book:
            return obj.book.discount_percentage
        elif obj.material:
            return obj.material.discount_percentage
        return None

    def get_discounted_price(self, obj):
        if obj.book:
            return obj.book.discounted_price
        elif obj.material:
            return obj.material.discounted_price
        return None

    def get_average_ratings(self, obj):
        if obj.book:
            return obj.book.average_ratings
        elif obj.material:
            return obj.material.average_ratings
        return None

    def get_availability(self, obj):
        if obj.book:
            return obj.book.availability
        elif obj.material:
            return obj.material.availability
        return None

class BooksCartSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()
    average_ratings = serializers.SerializerMethodField()

    class Meta:
        model = Books
        fields = [
            "id", 
            "name", 
            "price", 
            "discount_percentage", 
            "discounted_price", 
            "average_ratings", 
            "image", 
            "availability"
        ]
    
    def get_discounted_price(self, obj):
        return obj.discounted_price
    
    def get_average_ratings(self, obj):
        return obj.average_ratings
    

class MaterialsCartSerializer(serializers.ModelSerializer):
    discounted_price = serializers.SerializerMethodField()
    average_ratings = serializers.SerializerMethodField()

    class Meta:
        model = Materials
        fields = [
            "id", 
            "name", 
            "type",
            "price", 
            "discount_percentage", 
            "discounted_price", 
            "average_ratings", 
            "image", 
            "availability",
            "title"
        ]
    
    def get_discounted_price(self, obj):
        return obj.discounted_price
    
    def get_average_ratings(self, obj):
        return obj.average_ratings


class CartSerializer(serializers.ModelSerializer):
    book = BooksCartSerializer(read_only=True)
    material = MaterialsCartSerializer(read_only=True)
    
    class Meta:
        model = Cart
        fields = ["id", "quantity", "created_on", "book", "material"]


# ODERS MODULE SERIALIZERS *******
class OrderItemSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'quantity', 'price', 'name', 'image', 'discounted_price']

    def get_name(self, obj):
        if obj.book:
            return obj.book.name
        elif obj.material:
            return obj.material.name
        return None

    def get_image(self, obj):
        request = self.context["request"]
        if obj.book:
            return request.build_absolute_uri(obj.book.image.url)
        elif obj.material:
            return request.build_absolute_uri(obj.material.image.url)
        return None

    def get_discounted_price(self, obj):
        if obj.book:
            return obj.book.discounted_price
        elif obj.material:
            return obj.material.discounted_price
        return None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'created_on', 'total_price', 'status', 'items']

    def get_total_price(self, obj):
        return sum(item.price * item.quantity for item in obj.items.all())