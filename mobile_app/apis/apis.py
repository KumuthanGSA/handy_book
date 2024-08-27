from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count

# Third party imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# local imports
from core.apis.helpers import listdistinctfieldvalues
from core.apis.serializers import BooksActivitySerializer, EventsActivitySerializer, MaterialsActivitySerializer, ProfessionalsActivitySerializer
from mobile_app.models import Cart, Favorite, Order, OrderItem, Payment
from .serializers import AddBooksReviewSerializer, AddCartSerializer, AddFavoriteSerializer, AddMaterialsReviewSerializer, AddProfessionalsReviewSerializer, AddressCreateListSerializer, AddressUpdateSerializer, BooksDetaledRetrieveSerializer, BooksListSerializer, CartItemSerializer, CartSerializer, EditUserProfileSerializer, HomeSearchSerializer, ListMaterialsSerializer, MaterialsDetailedRetrieveSerializer, OrderSerializer, ProfessionalsDetailSerializer, RemoveFavoriteSeializer, ThirdPartySigninSerializer, ThirdPartySignupSerializer, TopBrandsListSerializer, UpdateCartQuantitySerializer, UserLogoutSerializer, UserRegisterSerializer, GetOTPSerializer, OTPVerficationSerializer, ProfessionalsListSerializer
from .pagination import BooksPagination, FavoritesPagination, MaterialsPagination, ProfessionalsPagination, TopBrandsPafination
from core.models import Addresses, Books, Events, Materials, MobileUsers, CustomUser, Professionals
from core.apis.permissions import IsAuthenticatedAndInUserGroup


# Create your apis here.
# USERS MANAGEMENT API'S
class UserRegisterView(APIView):
    """
    API endpoint where new user can register
    """

    def post(self, request):
        referral_code = request.query_params.get("referral_code")
        serializer = UserRegisterSerializer(data=request.data, context={"referral_code": referral_code})
        if serializer.is_valid():
            user, message = serializer.save()

            return Response({'detail': message}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UserGetOTPView(APIView):
    """
    API endpoint to generate otp.
    """

    def post(self, request):
        serializer = GetOTPSerializer(data=request.data)
        if serializer.is_valid():
            
            user = serializer.save()
            return Response({"detail": "OTP send successfully!", "otp": user.otp}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class UserOTPVerificationView(APIView):
    """
    To verify the given otp.
    """

    def post(self, request):
        serializer = OTPVerficationSerializer(data=request.data)
        if serializer.is_valid():

            token = serializer.save()
            return Response(token, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class UserLogoutView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request):
        serializer = UserLogoutSerializer(data=request.data)
        if serializer.is_valid():
            
            serializer.save()
            return Response({"detail": "Admin logged out successfully!"}, status=status.HTTP_200_OK)
            
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class EditUserProfileView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        user = get_object_or_404(MobileUsers, user=request.user)

        serializer = EditUserProfileSerializer(user)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        user = get_object_or_404(MobileUsers, user=request.user)

        serializer = EditUserProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "User updated successfully!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ThirdPartySignupView(APIView):
    def post(self, request):
        referral_code = request.query_params.get("referral_code")
        serializer = ThirdPartySignupSerializer(data=request.data, context={"referral_code": referral_code})
        if serializer.is_valid():
            user, message = serializer.save()

            return Response({'detail': message}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ThirdPartySigninView(APIView):
    def post(self, request):
        serializer = ThirdPartySigninSerializer(data=request.data)
        if serializer.is_valid():
            
            tokens = serializer.save()
            return Response(tokens, status=status.HTTP_202_ACCEPTED)  
          
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

# REFERRALS MODULE APIS ******
class ReferralsRetrieveView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        """
        API endpoint to get current user referral details 
        """
         
        user = get_object_or_404(MobileUsers, user_id=request.user.id)

        data = {
            "total_referrals": user.total_referrels,
            "referral_code": user.referral_code,
            "share_link": request.build_absolute_uri(f'register?referral_code={user.referral_code}')
        }

        return Response(data, status=status.HTTP_200_OK)


# HOME PAGE APIS *******
class NewListingsView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        activities = {
            "professionals": [],
            "materials": [],
            "events": [],
            "books": [],
        }

        professionals = Professionals.objects.all().order_by('-created_on')[:15]
        materials = Materials.objects.all().order_by('-created_on')[:15]
        events = Events.objects.all().order_by('-created_on')[:15]
        books = Books.objects.all().order_by('-created_on')[:15]


        activities["professionals"] =  ProfessionalsActivitySerializer(professionals, many=True).data
        activities["materials"] = MaterialsActivitySerializer(materials, many=True).data
        activities["events"] = EventsActivitySerializer(events, many=True).data
        activities["books"] = BooksActivitySerializer(books, many=True).data
        

        return Response(activities, status=status.HTTP_200_OK)
    

class TopBrandsListAPIView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        top_brands = Materials.objects.values('supplier_name').annotate(
            average_rating=Avg('reviews__rating'),
            material_count=Count('id')
        ).filter(material_count__gt=0).order_by('-average_rating')

        paginator = TopBrandsPafination()
        paginated_brands = paginator.paginate_queryset(top_brands, request)
        serializer = TopBrandsListSerializer(paginated_brands, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class HomeSearchView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        serializer = HomeSearchSerializer(data=request.query_params, context={"user": request.user})
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# Professionals******
class ListProfessinalsView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        """
        List all professionals.
        """
        expertise = request.query_params.get("expertise", None)
        location = request.query_params.get("location", None)
        search = request.query_params.get("search", None)
        if search:
            search = search.strip()

        if not expertise and not location and not search:
            professionals = Professionals.objects.all()

        else:
            filters = Q()
            if expertise:
                filters &= Q(expertise=expertise)

            if location:
                filters &= Q(location=location)

            if search:
                filters &= Q(name__icontains=search) | Q(email__icontains=search)

            professionals = Professionals.objects.filter(filters)

        pagination = ProfessionalsPagination()
        paginated_professionals = pagination.paginate_queryset(professionals, request)
        serializer = ProfessionalsListSerializer(paginated_professionals, many=True, context={"user": request.user})
        return pagination.get_paginated_response(serializer.data)
    

class ProfessionalsDetailView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request, pk):
        """
        API endpoint to get detailed view of a specific user.
        """

        professional = get_object_or_404(Professionals, id=pk)

        serializer = ProfessionalsDetailSerializer(professional, context={'user': request.user})

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AddProfessionalReviewView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request, pk):
        data = request.data.copy()

        data["professional"] = pk
        data["created_by"] = request.user.id

        serializer = AddProfessionalsReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Review added successfully1"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ListExpertiseView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        return Response({"detail": listdistinctfieldvalues(Professionals, "expertise")}, status=status.HTTP_200_OK)
    

class LocationListView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        return Response({"detail": listdistinctfieldvalues(Professionals, "location")} , status=status.HTTP_200_OK)
    

# Materials APIS *******
class CategoryMaterialsListView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        materials = listdistinctfieldvalues(Materials, "type")

        response = []

        for material in materials:
            data = {}
            instances = Materials.objects.filter(type=material)[:15]
            data["category"] = material
            data["items"] =  ListMaterialsSerializer(instances, many=True, context={"user": request.user}).data
            response.append(data)

        return Response({"data":response}, status=status.HTTP_200_OK)
    

class MaterialsDetailedView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self,request, pk):
        """
        API Endpoint for detailed material retrieve. 
        """

        material = get_object_or_404(Materials, id=pk)

        serializer = MaterialsDetailedRetrieveSerializer(material, context={'user': request.user})

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MaterialsListFiltersView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        rating = request.query_params.get("rating", None)
        type = request.query_params.get("category", None)
        supplier_name = request.query_params.get("brand", None)
        search = request.query_params.get("search", None)

        if not type and not supplier_name and not search and not rating:
            materials = Materials.objects.all()

        else:
            filters = Q()
            if rating:
                try:
                    rating = float(rating)  
                    if rating < 1 or rating > 5:
                        return Response({"detail": "Rating must be between 1 and 5"}, status=400)
                except ValueError:
                     return Response({"detail": "Invalid rating value"}, status=400)
                
                materials_with_avg_rating = Materials.objects.annotate(
                    avg_rating=Avg('reviews__rating')
                ).filter(avg_rating=rating)

                filters &= Q(id__in=materials_with_avg_rating.values('id'))
                
            if type:
                filters &= Q(type=type)

            if supplier_name:
                filters &= Q(supplier_name=supplier_name)

            if search:
                filters &= Q(supplier_name__icontains=search) | Q(type__icontains=search) | Q(name__icontains=search)

            materials = Materials.objects.filter(filters).distinct()

        pagination = MaterialsPagination()
        paginated_materials = pagination.paginate_queryset(materials, request)
        serializer = ListMaterialsSerializer(paginated_materials, many=True, context={"user": request.user})
        return pagination.get_paginated_response(serializer.data)
    

class AddMaterialsReviewView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request, pk):
        data = request.data.copy()
        mobile_user = get_object_or_404(MobileUsers, user=request.user)

        data["material"] = pk
        data["created_by"] = mobile_user.id

        serializer = AddMaterialsReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Review added successfully!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class MaterialsTypeListView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        return Response({"detail": listdistinctfieldvalues(Materials, "type")}, status=status.HTTP_200_OK)
    

class MaterialsSupplierListView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        return Response({"detail": listdistinctfieldvalues(Materials, "supplier_name")}, status=status.HTTP_200_OK)
    

# BOOKS APIS *******
class ListBooksView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request):
        """
        List all books.
        """
        search = request.query_params.get("search")

        if search:
            books = Books.objects.filter(name__icontains=search)
        else:
            books = Books.objects.all()

        pagination = BooksPagination()
        paginated_books = pagination.paginate_queryset(books, request)
        serializer = BooksListSerializer(paginated_books, many=True)
        return pagination.get_paginated_response(serializer.data)


class BooksDetailedRetrieveView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]
    
    def get(self,request, pk):
        """
        API Endpoint for detailed book retrieve. 
        """

        book = get_object_or_404(Books, id=pk)

        serializer = BooksDetaledRetrieveSerializer(book)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class AddBooksReviewView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request, pk):
        data = request.data.copy()
        mobile_user = get_object_or_404(MobileUsers, user=request.user)

        data["book"] = pk
        data["created_by"] = mobile_user.id

        serializer = AddBooksReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Review added successfully!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# ADDRESS MODULE APIS *******
class AddressCreateListView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request):
        mobile_user = get_object_or_404(MobileUsers, user=request.user)

        data = request.data.copy()
        data["user"] = mobile_user.id

        serializer = AddressCreateListSerializer(data=data)
        if serializer.is_valid():

            address_data = serializer.validated_data
            is_default = address_data.get('is_default', False)
            print(is_default, "chech here")
            if is_default:
                print(is_default, "second here")
                Addresses.objects.filter(user=mobile_user, is_default=True).update(is_default=False)

            serializer.save()

            return Response({"detail": "Address added successfully!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    def get(self, request):
        mobile_user = get_object_or_404(MobileUsers, user=request.user)
        addresses = Addresses.objects.filter(user=mobile_user)

        serializer = AddressCreateListSerializer(addresses, many=True)

        return Response({"detail": serializer.data}, status=status.HTTP_200_OK)


class AddressRetrieveUpdateView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def get(self, request, pk):
        address = get_object_or_404(Addresses, id=pk)

        serializer = AddressCreateListSerializer(address)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        address = get_object_or_404(Addresses, id=pk)

        serializer = AddressUpdateSerializer(address, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Address updated successfully!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

# Favorite Module *******
class FavoriteAddListView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request):
        mobile_user = get_object_or_404(MobileUsers, user=request.user)

        data = request.data.copy()
        data["user"] = mobile_user.id

        serializer = AddFavoriteSerializer(data=data, context={"request": request, "mobile_user": mobile_user})
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Favorite added successfully!"}, status=status.HTTP_201_CREATED)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        user = get_object_or_404(MobileUsers, user=request.user)
        type = request.query_params.get("type")

        # Helper function to get favorite ids based on type
        def get_favorite_ids(type):
            return Favorite.objects.filter(user=user, type=type).values_list('item_id', flat=True)

        # Helper function to paginate and serialize data
        def get_paginated_data(queryset, serializer_class):
            pagination = FavoritesPagination()
            paginated_queryset = pagination.paginate_queryset(queryset, request)
            serializer = serializer_class(paginated_queryset, many=True, context={'request': request})
            return pagination.get_paginated_response(serializer.data)

        if type == "professional":
            favorite_ids = get_favorite_ids('professional')
            queryset = Professionals.objects.filter(id__in=favorite_ids).order_by('-created_on')
            return get_paginated_data(queryset, ProfessionalsActivitySerializer)

        elif type == "material":
            favorite_ids = get_favorite_ids('material')
            queryset = Materials.objects.filter(id__in=favorite_ids).order_by('-created_on')
            return get_paginated_data(queryset, MaterialsActivitySerializer)

        elif type == "book":
            favorite_ids = get_favorite_ids('book')
            queryset = Books.objects.filter(id__in=favorite_ids).order_by('-created_on')
            return get_paginated_data(queryset, BooksActivitySerializer)

        elif not type:
            professionals_ids = get_favorite_ids('professional')
            books_ids = get_favorite_ids('book')
            materials_ids = get_favorite_ids('material')

            professionals = Professionals.objects.filter(id__in=professionals_ids).order_by('-created_on')[:15]
            books = Books.objects.filter(id__in=books_ids).order_by('-created_on')[:15]
            materials = Materials.objects.filter(id__in=materials_ids).order_by('-created_on')[:15]

            professionals_data = ProfessionalsActivitySerializer(professionals, many=True).data
            books_data = BooksActivitySerializer(books, many=True).data
            materials_data = MaterialsActivitySerializer(materials, many=True).data

            response_data = {
                "professionals": professionals_data,
                "materials": materials_data,
                "books": books_data,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        else:
            return Response({"detail": "Invalid type value"}, status=status.HTTP_400_BAD_REQUEST)


class RemoveFavoriteView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request):
        user = get_object_or_404(MobileUsers, user=request.user)
        
        item_type = request.data.get('type')
        item_id = request.data.get('item_id')

        serializer = RemoveFavoriteSeializer(data=request.data)
        if serializer.is_valid():

            favorite = Favorite.objects.filter(user=user, type=item_type, item_id=item_id).first()
            if not favorite:
                return Response({"detail": "Favorite not found."}, status=status.HTTP_400_BAD_REQUEST)

            favorite.delete()
            return Response({"detail": "Favorite removed successfully!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# CART MODULE APIS *******
class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(MobileUsers, user=request.user)

        serializer = AddCartSerializer(data=request.data)
        if serializer.is_valid():
            item_type = serializer.validated_data.get('type')
            item_id = serializer.validated_data.get('item_id')
            quantity = serializer.validated_data.get('quantity', 1)

            if item_type == 'book':
                try:
                    item = Books.objects.get(id=item_id)
                except Books.DoesNotExist:
                    return Response({"detail": "Book not found"}, status=status.HTTP_404_NOT_FOUND)
                
                # Check if item already exists in the cart
                cart_item = Cart.objects.filter(user=user, book=item).first()
                if cart_item:
                    cart_item.quantity += quantity
                    cart_item.save()
                    return Response({"detail": "Item count increased successfully!"}, status=status.HTTP_200_OK)
                else:
                    Cart.objects.create(user=user, book=item, quantity=quantity)
                    return Response({"detail": "New book added to cart successfully!"}, status=status.HTTP_200_OK)

            elif item_type == 'material':
                try:
                    item = Materials.objects.get(id=item_id)
                except Materials.DoesNotExist:
                    return Response({"detail": "Material not found"}, status=status.HTTP_404_NOT_FOUND)
                
                # Check if item already exists in the cart
                cart_item = Cart.objects.filter(user=user, material=item).first()
                if cart_item:
                    cart_item.quantity += quantity
                    cart_item.save()
                    return Response({"detail": "Item count increased successfully!"}, status=status.HTTP_200_OK)
                else:
                    Cart.objects.create(user=user, material=item, quantity=quantity)
                    return Response({"detail": "New material added to cart successfully!"}, status=status.HTTP_200_OK)

            else:
                return Response({"detail": "Invalid item type"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, *args, **kwargs):
        user = get_object_or_404(MobileUsers, user=request.user)
        cart_items = Cart.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"detail": "Cart is empty"}, status=status.HTTP_200_OK)

        serializer = CartSerializer(cart_items, many=True)
        return Response({"detail": serializer.data}, status=status.HTTP_200_OK)

    
    def patch(self, request, *args, **kwargs):
        user = get_object_or_404(MobileUsers, user=request.user)
        
        serializer = UpdateCartQuantitySerializer(data=request.data)
        if serializer.is_valid():

            item_type = serializer.validated_data.get('type')
            item_id = serializer.validated_data.get('item_id')
            quantity = serializer.validated_data.get('quantity')

            if item_type == 'book':
                try:
                    item = Books.objects.get(id=item_id)
                    cart_item = Cart.objects.filter(user=user, book=item).first()
                except Books.DoesNotExist:
                    return Response({"detail": "Book not found"}, status=status.HTTP_400_BAD_REQUEST)
                
            elif item_type == 'material':
                try:
                    item = Materials.objects.get(id=item_id)
                    cart_item = Cart.objects.filter(user=user, material=item).first()
                except Materials.DoesNotExist:
                    return Response({"detail": "Material not found"}, status=status.HTTP_400_BAD_REQUEST)

            if not cart_item:
                return Response({"detail": "Item not found in cart"}, status=status.HTTP_400_BAD_REQUEST)

            if quantity <= 0:
                cart_item.delete()
                return Response({"detail": "Item removed from cart"}, status=status.HTTP_200_OK)

            cart_item.quantity = quantity
            cart_item.save()

            return Response({"detail": "Item quantity updated successfully!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, *args, **kwargs):
        user = get_object_or_404(MobileUsers, user=request.user)

        serializer = AddCartSerializer(data=request.data)
        if serializer.is_valid():
            item_type = serializer.validated_data.get('type')
            item_id = serializer.validated_data.get('item_id')

            if item_type == 'book':
                cart_item = Cart.objects.filter(user=user, book_id=item_id).first()

            elif item_type == 'material':
                cart_item = Cart.objects.filter(user=user, material_id=item_id).first()

            if not cart_item:
                return Response({"detail": "Item not found in cart"}, status=status.HTTP_400_BAD_REQUEST)

            cart_item.delete()
            return Response({"detail": "Item removed from cart"}, status=status.HTTP_200_OK)
  

# ORDERS MODULE APIS *******
class CreateOrderAPI(APIView):
    permission_classes = [IsAuthenticatedAndInUserGroup]

    def post(self, request, *args, **kwargs):
        address_id = request.data.get("address_id")
        cart_ids = request.data.get("cart_ids")
        user = get_object_or_404(MobileUsers, user=request.user)
        address = get_object_or_404(Addresses, user=user, id=address_id)
        payment_type = request.data.get("payment_type")


        cart_items = Cart.objects.filter(id__in=cart_ids)
        
        if not cart_items.exists():
            return Response({"detail": "Cart does not contains those items"}, status=status.HTTP_400_BAD_REQUEST)
        
        order = Order.objects.create(user=user, total_price=0, address=address)

        total_price = 0
        for cart_item in cart_items:
            if cart_item.book:
                item_price = cart_item.book.discounted_price
            elif cart_item.material:
                item_price = cart_item.material.discounted_price
            else:
                continue
            
            OrderItem.objects.create(
                order=order,
                book=cart_item.book,
                material=cart_item.material,
                quantity=cart_item.quantity,
                price=item_price
            )
            total_price += item_price * cart_item.quantity
        
        order.total_price = total_price
        order.save()
        payment = Payment.objects.create(order=order, type=payment_type, status='pending', amount=total_price)

        # Clear the cart
        cart_items.delete()

        return Response({"order_id": order.id, "message": "Order Confirmed"}, status=status.HTTP_200_OK)