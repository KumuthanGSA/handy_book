import datetime
from django.db import transaction
from django.db.models import Avg
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.core.validators import MinValueValidator, MaxValueValidator

# Third party imports
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from phonenumber_field.serializerfields import PhoneNumberField

# Local imports
from core.models import Books, BooksReview, CustomUser, AdminUsers, Events, Materials, MaterialsReview, MobileUsers, Notifications, PortfolioImages, Portfolios, Professionals, ProReview, Transactions

# Create your serializers here

# ADMIN MANAGEMENT SERIALIZERS
class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Check if the user exists
        try:
            admin_user = AdminUsers.objects.get(email=email)
        except AdminUsers.DoesNotExist:
            raise serializers.ValidationError({"email": 'User does not exists'})

        # Check the password
        if not admin_user.user.check_password(password):
            raise serializers.ValidationError({'password': 'Wrong password'})
        
        attrs['custom_user'] = admin_user.user
        return attrs
    
    def save(self):
        custom_user = self.validated_data['custom_user']

        # Generate tokens (using Simple JWT library)
        refresh = RefreshToken.for_user(custom_user)
        access = refresh.access_token 

        tokens = {
            'access': str(access),
            'refresh': str(refresh)
        }

        return tokens
    

class AdminLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def save(self):
        # Attempt to blacklist the refresh token to log out the user
        try:
            RefreshToken(self.validated_data['refresh']).blacklist()
        except Exception as e:
            raise serializers.ValidationError({"refresh": str(e)})
        
        return
    

# ACCOUNTSETTINGS SERIALIZERS
class AccountSettingsRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUsers
        fields = ["first_name", "last_name", "email", "phone_no", "designation", "image"]


class AccountSettingsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUsers
        fields = ["first_name", "last_name", "email", "phone_no", "designation"]

        extra_kwargs = {
            'phone_no': {'required': True, 'allow_blank': False, 'allow_null': False},
            'designation': {'required': True, 'allow_blank': False, 'allow_null': False}
        }


class AccountSettingsProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUsers
        fields = ["image"]
    
        extra_kwargs = {
            'image': {'required': True, 'allow_null': False}
        }


class AdminChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context['request'].user

        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Check if the current password is correct
        if not user.check_password(current_password):
            raise serializers.ValidationError({'current_password': 'Wrong password'})
        
        # Check if new password and confirm password match
        if new_password != confirm_password:
            raise serializers.ValidationError({'confirm_password': 'Passwords mismatch'})
        
        # Validate the new password
        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': e.messages})
        
        return data
    
    def save(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()
        return user
    

# PROFESSIONALS MODULE SERIALIZERS
class ProfessionalsCreateRetrieveSerializer(serializers.ModelSerializer):
    review = serializers.CharField(write_only=True)
    rating = serializers.IntegerField(write_only=True)

    class Meta:
        model = Professionals
        fields = ['name', 'phone_no', 'email', 'expertise', 'location', 'about', 'experiance', 'review', 'rating', 'banner', 'website']

    def create(self, validated_data):
        review = validated_data.pop('review')
        rating = validated_data.pop('rating')
        request = self.context.get('request')

        location = validated_data["location"].title()
        expertise = validated_data["expertise"].title()

        validated_data["location"] = location
        validated_data["expertise"] = expertise

        # Roll back if any error occurs
        with transaction.atomic():
            professional = Professionals.objects.create(**validated_data)
            ProReview.objects.create(professional=professional, review=review, rating=rating, created_by=request.user)

        return professional
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        id = self.context.get("id")
        admin_review = get_object_or_404(ProReview, professional_id=id, created_by__is_superuser=True)

        representation['review'] = admin_review.review
        representation['rating'] = admin_review.rating

        return representation
    

class ProfessionalsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professionals
        fields = ['id', 'name', 'phone_no', 'email', 'expertise', 'location']


class ProfessionalsDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class ProfessionalsUpdateSerializer(serializers.ModelSerializer):
    review = serializers.CharField(write_only=True)
    rating = serializers.IntegerField(write_only=True)

    class Meta:
        model = Professionals
        fields = ['name', 'phone_no', 'email', 'expertise', 'location', 'about', 'experiance', 'review', 'rating', 'banner', 'website']

        extra_kwargs ={
            "website": {"required": True},
            "banner": {"required": False}
        }

    def update(self, instance, validated_data):
        id = self.context.get("id")
        review_data = validated_data.pop('review', None)
        rating_data = validated_data.pop('rating', None)    

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        admin_review = get_object_or_404(ProReview, professional_id=id, created_by__is_superuser=True)
        admin_review.review = review_data
        admin_review.rating = rating_data

        with transaction.atomic():
            instance.save()
            admin_review.save()

        return instance
    

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

    class Meta:
        model = Professionals
        fields = [
            'name', 'phone_no', 'email', 'expertise', 'location', 'about', 'experiance', 
            'banner', 'website', 'created_on', 'last_edited', 'portfolios', 'reviews', 
            'average_ratings'
        ]

    def get_average_ratings(self, obj):
        average_rating = obj.review_professional.aggregate(Avg('rating'))['rating__avg']

        return average_rating if average_rating is not None else 0
    
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


class PortfoliosCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=250)
    images = serializers.ListField(child=serializers.ImageField())
    professional_id = serializers.IntegerField()

    def validate(self, attrs):
        errors = {}

        try:
            professional = Professionals.objects.get(id=attrs["professional_id"])
            attrs["professional"] = professional
        except:
            errors.setdefault("id", []).append("Id does not exist.")

        if errors:
            raise serializers.ValidationError(errors)
        
        return attrs
    
    def create(self, validated_data):
        title = self.validated_data["title"]
        professional = self.validated_data["professional"]
        images = validated_data.pop('images')
        
        portfolio = Portfolios.objects.create(professional=professional, title=title)

        for image in images:
            PortfolioImages.objects.create(portfolio=portfolio, image=image)

        return portfolio
    
    
class PortfoliosImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioImages
        fields = ["id", "image"]

class PortfoliosListSerializer(serializers.ModelSerializer):
    images = PortfoliosImagesSerializer(many=True, read_only=True)
    title_id = serializers.SerializerMethodField()

    class Meta:
        model = Portfolios
        fields = ['title_id', 'title', 'images']
    
    def get_title_id(self, obj):
        return obj.id


class PortfoliosDeleteSerializer(serializers.Serializer):
    title_id = serializers.IntegerField()

    def validate(self, attrs):
        errors = {}

        try:
            portfolio = Portfolios.objects.get(id=attrs["title_id"])
            attrs["portfolio"] = portfolio

        except Portfolios.DoesNotExist:
            errors.setdefault("id", []).append("Id does not exist.")

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
    

class PortfoliosImagesDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate(self, attrs):
        errors = {}

        try:
            image = PortfolioImages.objects.get(id=attrs["id"])
            attrs["image"] = image

        except Portfolios.DoesNotExist:
            errors.setdefault("id", []).append("Id does not exist.")

        if errors:
            raise serializers.ValidationError(errors)

        return attrs
    

class PortfoliosUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title_id = serializers.IntegerField()
    title = serializers.CharField(max_length=250)
    images = serializers.ListField(child=serializers.ImageField(), required=False)

    def validate(self, attrs):
        errors = {}

        try:
            professional = Professionals.objects.get(id=attrs["id"])
            attrs["professional"] = professional

        except Professionals.DoesNotExist:
            errors.setdefault("id", []).append("Id does not exist.")
            raise serializers.ValidationError(errors)
        
        try:
            portfolio = Portfolios.objects.get(professional=professional, id=attrs["title_id"])      
            attrs["portfolio"] = portfolio

        except Portfolios.DoesNotExist:
            errors.setdefault("title_id", []).append("ID does not exist.")
        
        if errors:
            raise serializers.ValidationError(errors)
        
        return attrs
    
    def save(self):
        title_id = self.validated_data["title_id"]
        title = self.validated_data["title"]
        images = self.validated_data.get("images", [])
        portfolio = self.validated_data["portfolio"]
        professional = self.validated_data["professional"]

        if not portfolio.title == title:
            portfolio.title=title
            portfolio.save()

        for image in images:
            portfolio_images = PortfolioImages.objects.create(portfolio=portfolio, image=image)

        return portfolio


# BOOKS MODULE SERIALIZERS *******
class BooksCreateRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = ["name", "price", "description", "additional_details", "image", "availability", "discount_percentage"]

        extra_kwargs ={
            "availability": {"required": True}
        }


class BooksUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = ["name", "price", "description", "additional_details", "image", "availability", "discount_percentage"]

        extra_kwargs ={
            "availability": {"required": True},
            "image": {"required": False}
        }
    

class BooksListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = ["id", "image", "name", "price", "availability"]


class BooksMultipleDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


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
            "average_ratings"
        ]

    def get_average_ratings(self, obj):
        average_rating = obj.reviews.aggregate(Avg('rating'))['rating__avg']

        return average_rating if average_rating is not None else 0
    
    def get_discounted_price(self, obj):
        if obj.discount_percentage == 0 or not obj.discount_percentage:
            return obj.price
        
        return obj.price - (obj.discount_percentage * obj.price)/100


# EVENTS MODULE SERIALIZERS *******
class EventsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ["title", "date", "location", "description", "image", "additional_informations"]


class EventsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ["id", "title", "date", "location"]


class EventsMultipleDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class EventsRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = ["title", "date", "location", "description", "image", "additional_informations"]

        extra_kwargs ={
            "additional_informations": {"required": True},
            "image": {"required": False}
        }


# MATERIALS MODULE SERIALIZERS *******
class MaterialsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materials
        fields = ["name", "type", "supplier_name", "supplier_phone_no", "price", "discount_percentage", "title", "availability", "image", "description", "overview", "additional_details"]


class MaterialsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materials
        fields = ["id", "name", "image", "type", "supplier_name", "supplier_phone_no", "price", "availability"]


class MaterialsMultipleDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


class MaterialsRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materials
        fields = ["name", "type", "supplier_name", "supplier_phone_no", "price", "discount_percentage", "title", "availability", "image", "description", "overview", "additional_details"]

        extra_kwargs ={
            "availability": {"required": True},
            "overview": {"required": True},
            "additional_details": {"required": True},
            "image": {"required": False}
        }


class MaterialsReviewsSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.first_name")
    role = serializers.CharField(default="client")
    class Meta:
        model = MaterialsReview
        fields = ["created_by_name", "rating", "review", "role"]


class MaterialsDetailedRetrieveSerializer(serializers.ModelSerializer):
    reviews = MaterialsReviewsSerializer(many=True, read_only=True)
    average_ratings = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Materials
        fields = [
            "name", 
            "type", 
            "supplier_name", 
            "supplier_phone_no", 
            "price", 
            "discount_percentage", 
            "discounted_price", 
            "title", 
            "availability", 
            "image", 
            "description", 
            "overview", 
            "additional_details", 
            "created_on", "last_edited", "reviews", "average_ratings"
        ]

    def get_average_ratings(self, obj):
        average_rating = obj.reviews.aggregate(Avg('rating'))['rating__avg']

        return average_rating if average_rating is not None else 0
    
    def get_discounted_price(self, obj):
        if obj.discount_percentage == 0 or not obj.discount_percentage:
            return obj.price
        
        return obj.price - (obj.discount_percentage * obj.price)/100


# USERS MODULE SERIALIZERS
class UsersListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ["id", "first_name", "email", "phone_no", "created_on", "is_active"]


class UsersListCheckSerializer(serializers.Serializer):
    status = serializers.BooleanField(required=False, allow_null=True)
    search = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    from_date = serializers.DateTimeField(required=False, allow_null=True)
    to_date = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        from_date = attrs.get("from_date")
        to_date = attrs.get("to_date")

        if from_date or to_date:
            if not from_date or not to_date:
                raise serializers.ValidationError("both 'from_date' and 'to_date' is required")
        
        return attrs


class UsersMultipleDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())
        

class UsersRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ["id", "first_name", "email", "phone_no", "created_on", "image"]

        extra_kwargs = {
            'phone_no': {'required': True, 'allow_blank': False, 'allow_null': False},
            'created_on': {"required": True},
        }


class UsersUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ["first_name", "email", "phone_no", "created_on"]

        extra_kwargs = {
            'phone_no': {'required': True, 'allow_blank': False, 'allow_null': False},
            'created_on': {"required": True},
        }


class UsersProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        fields = ["image"]
    
        extra_kwargs = {
            'image': {'required': True, 'allow_null': False}
        }


# TRANSACTIONS MODULE SERIALIZERS *******
class TransactionsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = ["id", "created_on", "user_involved", "type", "amount", "status"]


class TransactionsListCheckSerializer(serializers.Serializer):
    type = serializers.CharField(required=False, allow_null=True)
    search = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    from_date = serializers.DateTimeField(required=False, allow_null=True)
    to_date = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        from_date = attrs.get("from_date")
        to_date = attrs.get("to_date")

        if from_date or to_date:
            if not from_date or not to_date:
                raise serializers.ValidationError("both 'from_date' and 'to_date' is required")
            
        return attrs

class TransactionsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = "__all__"


class TransactionsMarkAsCompletedSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField())


# DASHBOARD SERIALIZERS *******
class  ProfessionalsGrowthChartSerializer(serializers.Serializer):
    months = serializers.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12)
        ]
    )


class RevenueGrowthSerializer(serializers.Serializer):
    PERIODS_CHOICES = [('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')]
    periods = serializers.ChoiceField(choices=PERIODS_CHOICES)


class ProfessionalsActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Professionals
        fields = '__all__'
    
    
class BooksActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Books
        fields = "__all__"

    
class MaterialsActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Materials
        fields = "__all__"

    
class EventsActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Events
        fields = "__all__"


class MobileUsersActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileUsers
        exclude = ['user', 'is_active']


class NotificationsActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = "__all__"


class TransactionsActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = "__all__"


class NotificationsCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ["title", "recipient", "status", "body", "image"]

        extra_kwargs = {
            "status": {"required": True}
        }


# NOTIFICATIONS MODULE SERIALIZERS *******
class NotificationsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ["id", "created_on", "title", "recipient", "body", "status"]


class NotificationsListCheckSerializer(serializers.Serializer):
    recipient = serializers.BooleanField(required=False, allow_null=True)
    search = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    from_date = serializers.DateTimeField(required=False, allow_null=True)
    to_date = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        from_date = attrs.get("from_date")
        to_date = attrs.get("to_date")

        if from_date or to_date:
            if not from_date or not to_date:
                raise serializers.ValidationError("both 'from_date' and 'to_date' is required")
            
        return attrs


class NotificationsRetrieveUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = ["recipient", "title", "body","status"]

        extra_kwargs = {
            "status": {"required": True}
        }

    def validate(self, data):
        instance = self.instance
        if instance and instance.status=='sent':
            raise serializers.ValidationError({"status": "Notification has already been sent and cannot be edited."}) 
        return data