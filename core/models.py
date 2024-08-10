import uuid
from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator

# Third party imports
from phonenumber_field.modelfields import PhoneNumberField

# Create your functions here
def generate_referral_code():
    code = str(uuid.uuid4())[:16]
    return code.upper() 

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        admin_user = AdminUsers.objects.create(email=email, user=user)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
    

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    username = None

    def __str__(self) -> str:
        return f' {self.id}'
    
    @property
    def related_user(self):
        try:
            return self.mobile_user
        except MobileUsers.DoesNotExist:
            try:
                return self.admin_user
            except AdminUsers.DoesNotExist:
                return None


class AdminUsers(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="admin_user")
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    email = models.EmailField(unique=True)
    designation = models.CharField(max_length=200, blank=True, null=True)
    phone_no = PhoneNumberField(region='IN', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f' {self.id} - {self.first_name}'
    

# USERS MODULE MODELS *******
class MobileUsers(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="mobile_user")
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_no = PhoneNumberField(region="IN", unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    fcm_token = models.TextField(blank=True, null=True)
    otp = models.CharField(max_length=4, null=True, blank=True)
    referral_code = models.CharField(max_length=16, unique=True)
    total_referrels = models.IntegerField(default=0)


    def __str__(self) -> str:
        return self.first_name
    
    @classmethod
    def count(cls):
        return cls.objects.count()
    

class Addresses(models.Model):
    TYPE_CHOICES = (('home', 'Home'), ('office', 'Office'), ('other', 'Other'))

    user = models.ForeignKey(MobileUsers, on_delete=models.CASCADE, related_name="adressses")
    type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='home')
    name = models.CharField(max_length=150)
    phone_no = PhoneNumberField(region="IN")
    pincode = models.IntegerField(validators=[MinValueValidator(100000), MaxValueValidator(999999)])
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=150)
    street = models.CharField(max_length=300)
    flat_no = models.CharField(max_length=300)
    landmark = models.CharField(max_length=500, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Referrals(models.Model):
    referrer = models.ForeignKey(MobileUsers, related_name='referrals', on_delete=models.CASCADE)
    referred = models.OneToOneField(MobileUsers, related_name='referred_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    created_on = models.DateField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __Str__(self):
        return self.referrer
    

# PROFESSIONALS MODULE MODELS *******
"""
Represents individual professionals, including their personal details and associated expertise.
"""
class Professionals(models.Model):
    name = models.CharField(max_length=150)
    phone_no = PhoneNumberField(region='IN', unique=True)
    email = models.EmailField(unique=True)
    expertise = models.CharField(max_length=250)
    location = models.CharField(max_length=150)
    about = models.TextField()
    experiance = models.TextField()
    banner = models.ImageField(upload_to='professionals/banners', blank=True, null=True)
    website = models.URLField(max_length=500, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f' {self.id} - {self.name}'
    
    @classmethod
    def count(cls):
        return cls.objects.count()
    
    @property
    def average_ratings(self):
        average_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return average_rating if average_rating is not None else 0


class Portfolios(models.Model):
    professional = models.ForeignKey(Professionals, on_delete=models.CASCADE, related_name="porfolios")
    title = models.CharField(max_length=250)
    image = models.ImageField(upload_to='professionals/portfolios')
    created_on = models.DateField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.professional} - {self.title}"


"""
Contains reviews for professionals, including ratings and comments.
"""
class ProReview(models.Model):
    created_by = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='reviewed_by')
    created_on = models.DateField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)
    professional = models.ForeignKey(Professionals, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['created_by', 'professional'], name='unique_created_by_professional')
        ]

    def __str__(self) -> str:
        return f' {self.id} - {self.review}'
    

# BOOKS MODULE MODELS *******
class Books(models.Model):
    AVAILABILITY_CHOICES = (('in stock', 'In Stock'), ('out of stock', 'Out of Stock'))
    name = models.CharField(max_length=300)
    price = models.FloatField()
    discount_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    description = models.TextField()
    additional_details = models.TextField()
    image = models.ImageField(upload_to='books',)
    availability = models.CharField(max_length=30, choices=AVAILABILITY_CHOICES, default='In Stock')
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f' {self.id} - {self.name}'
    
    @property
    def discounted_price(self):
        return self.price * (1 - self.discount_percentage / 100)
    
    @property
    def average_ratings(self):
        average_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return average_rating if average_rating is not None else 0
    

class BooksReview(models.Model):
    created_by = models.ForeignKey(MobileUsers, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='book_reviews')
    created_on = models.DateField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)
    book = models.ForeignKey(Books, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['created_by', 'book'], name='unique_created_by_book')
        ]

    def __str__(self) -> str:
        return f' {self.id} - {self.review}'
    

# EVENTS MODULE MODELS *******
class Events(models.Model):
    title = models.CharField(max_length=250)
    date = models.DateTimeField()
    location = models.CharField(max_length=150)
    description = models.TextField()
    image = models.ImageField(upload_to='events/',)
    additional_informations = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f' {self.id} - {self.title}'
    

# MATERIALS MODULE MODELS *******
class Materials(models.Model):
    AVAILABILITY_CHOICES = (('in stock', 'In Stock'), ('out of stock', 'Out of Stock'))
    
    name = models.CharField(max_length=250)
    type = models.CharField(max_length=250)
    supplier_name = models.CharField(max_length=250)
    supplier_phone_no = PhoneNumberField(region='IN')
    price = models.FloatField()
    discount_percentage = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    title = models.CharField(max_length=250)
    availability = models.CharField(max_length=30, choices=AVAILABILITY_CHOICES, default='in stock')
    image = models.ImageField(upload_to='materials/',)
    description = models.TextField()
    overview = models.TextField(blank=True, null=True)
    additional_details = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f' {self.id} - {self.name}'
    
    @classmethod
    def count(cls):
        return cls.objects.count()
    
    @property
    def discounted_price(self):
        return self.price * (1 - self.discount_percentage / 100)
    
    @property
    def average_ratings(self):
        average_rating = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return average_rating if average_rating is not None else 0
    

class MaterialsReview(models.Model):
    created_by = models.ForeignKey(MobileUsers, on_delete=models.DO_NOTHING, blank=True, null=True, related_name='material_reviews')
    created_on = models.DateField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)
    material = models.ForeignKey(Materials, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['created_by', 'material'], name='unique_created_by_material')
        ]

    def __str__(self) -> str:
        return f' {self.id} - {self.review}'
    

# TRANSACTIONS MODULE MODELS *******
class Transactions(models.Model):
    TYPE_CHOICES = (('payment', 'Payment'), ('refund', 'Refund'))
    STATUS_CHOICES = (('completed', 'Completed'), ('pending', 'Pending'))

    created_on = models.DateTimeField(auto_now=True)
    last_edited = models.DateTimeField(auto_now=True)
    user_involved = models.CharField(max_length=150)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    amount = models.FloatField()
    status = models.CharField(max_length=100, choices=STATUS_CHOICES)

    def __str__(self):
        return f'{self.user_involved} - {self.type}'
    
    @classmethod
    def count(cls):
        return cls.objects.count()
    

# NOTIFICATIONS MODULE MODELS *******
class Notifications(models.Model):
    RECIPIENT_CHOICES = [('all users', 'All Users')]
    STATUS_CHOICES = [('sent', 'Sent'), ('pending', 'Pending'), ('failed', 'Failed')]

    title = models.CharField(max_length=250)
    recipient =models.CharField(max_length=100, choices=RECIPIENT_CHOICES)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    body = models.TextField()
    image = models.ImageField(upload_to='notifications/')
    created_on = models.DateTimeField(auto_now_add=True)
    last_edited = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.id} - {self.status}"