from django.urls import path

# Third part imports
from rest_framework_simplejwt.views import TokenRefreshView

# Local imports
from .apis import AddBooksReviewView, AddToCartAPIView, EditUserProfileView, FavoriteAddListView, AddMaterialsReviewView, AddProfessionalReviewView, AddressRetrieveUpdateView, BooksDetailedRetrieveView, HomeSearchView, ListBooksView, ListExpertiseView, ListProfessinalsView, LocationListView, MaterialsDetailedView, MaterialsListFiltersView, CategoryMaterialsListView, MaterialsSupplierListView, MaterialsTypeListView, NewListingsView, ProfessionalsDetailView, ReferralsRetrieveView, RemoveFavoriteView, ThirdPartySigninView, ThirdPartySignupView, TopBrandsListAPIView, UserLogoutView, UserRegisterView, UserGetOTPView, UserOTPVerificationView, AddressCreateListView

urlpatterns = [
    # User management
    path('register', UserRegisterView.as_view()),
    path('getotp', UserGetOTPView.as_view()),
    path('validate_otp', UserOTPVerificationView.as_view()),
    path('refresh', TokenRefreshView.as_view(), name='user_token_refresh'),
    path('logout', UserLogoutView.as_view()),
    path('thirdpartysignup', ThirdPartySignupView.as_view()),
    path('thirdpartysignin', ThirdPartySigninView.as_view()),
    path('profile', EditUserProfileView.as_view()),

    # Referrals
    path('referrals', ReferralsRetrieveView.as_view()),

    # Home Page
    path('home/new_listings', NewListingsView.as_view()),
    path('home/serach', HomeSearchView.as_view()),
    path('home/top_brands', TopBrandsListAPIView.as_view()),

    # Professional
    path('professionals', ListProfessinalsView.as_view()),
    path('professionals/details/<int:pk>', ProfessionalsDetailView.as_view()),
    path('professionals/reviews/<int:pk>', AddProfessionalReviewView.as_view()),
    path('professionals/expertise', ListExpertiseView.as_view()),
    path('professionals/locations', LocationListView.as_view()),

    #Materials
    path('materials/details/<int:pk>', MaterialsDetailedView.as_view()),
    path('materials/category_products', CategoryMaterialsListView.as_view()),
    path('materials/filters', MaterialsListFiltersView.as_view()),
    path('materials/category', MaterialsTypeListView.as_view()),
    path('materials/brand', MaterialsSupplierListView.as_view()),
    path('materials/reviews/<int:pk>', AddMaterialsReviewView.as_view()),

    #Books
    path('books', ListBooksView.as_view()),
    path('books/details/<int:pk>', BooksDetailedRetrieveView.as_view()),
    path('books/reviews/<int:pk>', AddBooksReviewView.as_view()),

    #Addresses
    path('address', AddressCreateListView.as_view()),
    path('address/<int:pk>', AddressRetrieveUpdateView.as_view()),

    #Favorites
    path('favorites', FavoriteAddListView.as_view()),
    path('favorites/remove', RemoveFavoriteView.as_view()),

    #Cart
    path('cart', AddToCartAPIView.as_view()),
]