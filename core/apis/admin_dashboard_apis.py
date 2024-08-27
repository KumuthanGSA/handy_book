import datetime
import json
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Avg, Max
from django.db.models.aggregates import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.utils.timesince import timesince

# Third party imports
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Local imports
from .helpers import listdistinctfieldvalues
from .permissions import IsAuthenticatedAndAdmin, IsAuthenticatedAndInUserGroup
from .serializers import AdminLoginSerializer, AdminLogoutSerializer, AccountSettingsRetrieveSerializer, AccountSettingsUpdateSerializer, AccountSettingsProfilePictureSerializer, AdminChangePasswordSerializer, BooksActivitySerializer, BooksCreateRetrieveUpdateSerializer, BooksDetaledRetrieveSerializer, BooksListSerializer, BooksMultipleDeleteSerializer, BooksUpdateSerializer, EventsActivitySerializer, EventsCreateSerializer, EventsListSerializer, EventsMultipleDeleteSerializer, EventsRetrieveUpdateSerializer, MaterialsActivitySerializer, MaterialsCreateSerializer, MaterialsDetailedRetrieveSerializer, MaterialsListSerializer, MaterialsMultipleDeleteSerializer, MaterialsRetrieveUpdateSerializer, MobileUsersActivitySerializer, NotificationsActivitySerializer, NotificationsListCheckSerializer, NotificationsRetrieveUpdateSerializer, NotificationsCreateSerializer, NotificationsListSerializer, PortfoliosCreateSerializer, PortfoliosDeleteSerializer, PortfoliosImagesDeleteSerializer, PortfoliosListSerializer, PortfoliosUpdateSerializer, ProfessionalsActivitySerializer, ProfessionalsCreateRetrieveSerializer, ProfessionalsDeleteSerializer, ProfessionalsDetailSerializer, ProfessionalsGrowthChartSerializer, ProfessionalsListSerializer, ProfessionalsUpdateSerializer, RevenueGrowthSerializer, TransactionsActivitySerializer, TransactionsCreateSerializer, TransactionsListCheckSerializer, TransactionsListSerializer, TransactionsMarkAsCompletedSerializer, UsersListCheckSerializer, UsersListSerializer, UsersMultipleDeleteSerializer, UsersProfilePictureSerializer, UsersRetrieveSerializer, UsersUpdateSerializer
from . paginations import BooksPagination, EventsPagination, MaterialsPagination, NotificationsPagination, ProfessionalsPagination, TransactionsPagination, UsersPagination
from core.models import Books, CustomUser, AdminUsers, Events, Materials, MobileUsers, Notifications, Portfolios, Professionals, ProReview, Transactions
from core.apis.firebase import get_recipient_fcm_tokens, send_fcm_notification

# Create your views apis.
# ADMIN MANAGEMENT APIS
class AdminLoginView(APIView):
    """
    API endpoint for Admin login.
    Validates user credentials, active status and generates access and refresh tokens upon successful login.

    required params: email, password
    """

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            
            tokens = serializer.save()
            return Response(tokens, status=status.HTTP_202_ACCEPTED)  
          
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)       
     

class AdminLogoutView(APIView):
    """
    API endpoint to logout a Admin user by blacklisting their refresh token.

    required params: refresh
    """
    
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        serializer = AdminLogoutSerializer(data=request.data)
        if serializer.is_valid():
            
            serializer.save()
            return Response({"detail": "Admin logged out successfully!"}, status=status.HTTP_200_OK)
            
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ACCOUNT SETTINGS API'S *******
class AdminAccountSettingsView(APIView):
    # Ensure the view is accessible only to authenticated users in the 'Admin' group
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):
        """
        Retrive admin user profile
        """

        admin_user = get_object_or_404(AdminUsers, user=request.user)
        serializer = AccountSettingsRetrieveSerializer(admin_user, context={'request': request})

        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Allow authenticated admin users to update their profile information.
        """

        user = get_object_or_404(AdminUsers, user=request.user)

        serializer = AccountSettingsUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Profile updated successfully!!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """
        Allow authenticated admin users to update their profile picture.
        """

        user = get_object_or_404(AdminUsers, user=request.user)

        serializer = AccountSettingsProfilePictureSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Profile picture updated successfully!!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class AdminSecurityView(APIView):
    # Ensure the view is accessible only to authenticated users in the 'Admin' group
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        API endpoint that allows admin users to change their password.
        """
        
        serializer = AdminChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Password changed successfully!!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

# PROFESSIONALS MODULE API'S *******
class ProfessionalsListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        Creates a new Professional and its associated ADMIN review.
        """
        serializer = ProfessionalsCreateRetrieveSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
        
            professional = serializer.save()

            return Response({"detail": "Professional created successfully!!", "id": professional.id}, status=status.HTTP_201_CREATED)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
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
        serializer = ProfessionalsListSerializer(paginated_professionals, many=True)
        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple Profesionals and their corresponding reviews.
        """
        serializer = ProfessionalsDeleteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deleted_count, deleted_objects = Professionals.objects.filter(id__in=serializer.validated_data["ids"]).delete()
                professional_deleted_count = deleted_objects.get(Professionals._meta.label, 0)
                review_count, _ = ProReview.objects.filter(professional_id__in=serializer.validated_data["ids"]).delete()

                if deleted_count == 0:
                    return Response({"detail": "No Professionals were deleted"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{professional_deleted_count} Professionals deleted successfully!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST) 
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalsRetrieveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        Retrieve specific professional.
        """

        professional = get_object_or_404(Professionals, id=pk)

        serializer = ProfessionalsCreateRetrieveSerializer(professional, context={'request': request, 'id': pk})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Updates a specific Professional and its associated ADMIN review.
        """

        professional = get_object_or_404(Professionals, id=pk)

        serializer = ProfessionalsUpdateSerializer(professional, data=request.data, context={'request': request, 'id': pk})
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Professional updated successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
           
    def delete(self, request, pk):
        """
        Delets specific Professional and all its reviews.
        """
        # Retrieve and mark the Professional instance as deleted
        professional = get_object_or_404(Professionals, id=pk)
        try:
            professional.delete()
            return Response({"detail": "Professional deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class ProfessionalsPortfoliosCreateListUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request, pk):
        data = request.data
        data["professional_id"] = pk
        serializer = PortfoliosCreateSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Portfolio added successfully!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, pk):
        """
        Retrieve all Portfolios(titles) with their images 
        of a specific professional.
        """

        professional = get_object_or_404(Professionals, id=pk)
        portfolios = Portfolios.objects.filter(professional=professional)
        
        serializer = PortfoliosListSerializer(portfolios, many=True, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk):
        """
        Delete particular portfolio(title) with all corresponding
        images of a specific professional.
        """
        serializer = PortfoliosDeleteSerializer(data=request.data)
        if serializer.is_valid():
            portfolio = serializer.validated_data["portfolio"]
            try:
                deleted_count, deleted_objects = portfolio.delete()
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({"detail": "Portfolio deleted successfully!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        data = request.data.copy()
        data["id"] = pk

        serializer = PortfoliosUpdateSerializer(data=data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Portfolio updated successfully!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class PortfoliosImagesDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def delete(self, request, pk):
        """
        Delete specific image of a particular portofolio.
        """
        
        serializer = PortfoliosImagesDeleteSerializer(data={"id": pk})
        if serializer.is_valid():

            image = serializer.validated_data["image"]
            image.delete()

            return Response({"detail": "Image deleted succcessfully!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ProfessionalsDetailView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        API endpoint to get detailed view of a specific user.
        """

        professional = get_object_or_404(Professionals, id=pk)

        serializer = ProfessionalsDetailSerializer(professional, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)


class ListExpertiseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(listdistinctfieldvalues(Professionals, "expertise"), status=status.HTTP_200_OK)
    

class LocationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(listdistinctfieldvalues(Professionals, "location"), status=status.HTTP_200_OK)
        

# BOOKS MODULE API'S *******
class BooksListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        To create new book.
        """

        serializer = BooksCreateRetrieveUpdateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Book created successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
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
        serializer = BooksListSerializer(paginated_books, many=True, context={'request': request})
        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple books at the same time.
        """

        serializer = BooksMultipleDeleteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deleted_count, _ = Books.objects.filter(id__in=serializer.validated_data["ids"]).delete()

                if deleted_count == 0:
                    return Response({"detail": "No books were deactivated"}, status=status.HTTP_404_NOT_FOUND)
                
                return Response({"detail": f"{deleted_count} books deleted successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class BooksRetriveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        Retrieve specific book
        """

        book = get_object_or_404(Books, id=pk)
        serializer = BooksCreateRetrieveUpdateSerializer(book, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific book.
        """

        book = get_object_or_404(Books, id=pk)

        serializer = BooksUpdateSerializer(book, request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Book updated successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Delete specific book.
        """

        book = get_object_or_404(Books, id=pk)

        try:
            book.delete()
            return Response({"detail": "Book deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BooksDetailedRetrieveView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]
    
    def get(self,request, pk):
        """
        API Endpoint for detailed book retrieve. 
        """

        book = get_object_or_404(Books, id=pk)

        serializer = BooksDetaledRetrieveSerializer(book, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)


# EVENTS MODULE API'S
class EventsListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        To create new events.
        """

        serializer = EventsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Event created successfully!!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """
        List all events.
        """

        search = request.query_params.get("search")
        search = search.strip()

        if not search:
            events = Events.objects.all()
        
        else:
            events = Events.objects.filter(Q(title__icontains=search)|Q(location__icontains=search))
        
        pagination = EventsPagination()
        paginated_events = pagination.paginate_queryset(events, request)
        serializer = EventsListSerializer(paginated_events, many=True, context={'request': request})

        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple events at the same time.
        """

        serializer = EventsMultipleDeleteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deleted_count, _ = Events.objects.filter(id__in=serializer.validated_data["ids"]).delete()

                if deleted_count == 0:
                    return Response({"detail": "No events were deactivated"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{deleted_count} events deleted successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class EventsRetriveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        Retrieve specific material.
        """

        event = get_object_or_404(Events, id=pk)
        serializer = EventsRetrieveUpdateSerializer(event, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific material.
        """

        event = get_object_or_404(Events, id=pk)

        serializer = EventsRetrieveUpdateSerializer(event, request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Event updated successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Delete specific event.
        """

        event = get_object_or_404(Events, id=pk)

        try:
            event.delete()
            return Response({"detail": "Event deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

# MATERIALS MODULE APIS *******
class MaterialsListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        To create new material.
        """

        serializer = MaterialsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Material created successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """
        List all materials.
        """
        type = request.query_params.get("type", None)
        supplier_name = request.query_params.get("supplier_name", None)
        search = request.query_params.get("search", None)

        if not type and not supplier_name and not search:
            materials = Materials.objects.all()

        else:
            filters = Q()
            if type:
                filters &= Q(type=type)

            if supplier_name:
                filters &= Q(supplier_name=supplier_name)

            if search:
                filters &= Q(supplier_name__icontains=search) | Q(type__icontains=search) | Q(name__icontains=search)

            materials = Materials.objects.filter(filters)

        pagination = MaterialsPagination()
        paginated_materials = pagination.paginate_queryset(materials, request)
        serializer = MaterialsListSerializer(paginated_materials, many=True, context={"request": request})
        return pagination.get_paginated_response(serializer.data)
    
    def delete(self, request):
        """
        Delete multiple materials at the same time.
        """

        serializer = MaterialsMultipleDeleteSerializer(data=request.data)
        if serializer.is_valid():
            try:
                deleted_count, _ = Materials.objects.filter(id__in=serializer.validated_data["ids"]).delete()

                if deleted_count == 0:
                    return Response({"detail": "No material were deactivated"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{deleted_count} materials deleted successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class MaterialsRetriveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        Retrieve specific material.
        """

        material = get_object_or_404(Materials, id=pk)
        serializer = MaterialsRetrieveUpdateSerializer(material, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific material.
        """

        material = get_object_or_404(Materials, id=pk)

        serializer = MaterialsRetrieveUpdateSerializer(material, request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Material updated successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Delete specific material.
        """

        material = get_object_or_404(Materials, id=pk)
        try:
            material.delete()
            return Response({"detail": "Material deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

class MaterialsTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(listdistinctfieldvalues(Materials, "type"), status=status.HTTP_200_OK)
    

class MaterialsSupplierListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(listdistinctfieldvalues(Materials, "supplier_name"), status=status.HTTP_200_OK)
    

class MaterialsDetailedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request, pk):
        """
        API Endpoint for detailed material retrieve. 
        """

        material = get_object_or_404(Materials, id=pk)

        serializer = MaterialsDetailedRetrieveSerializer(material, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
        

# USERS MODULE APIS *******
class UsersListDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):
        """
        List all users.
        """

        serializer = UsersListCheckSerializer(data=request.query_params)
        if serializer.is_valid():

            status_ = serializer.validated_data.get("status", None)
            search = serializer.validated_data.get("search", None)
            from_date = serializer.validated_data.get("from_date", None)
            to_date = serializer.validated_data.get("to_date", None)

            if not from_date and not to_date and not search and status_ is None:
                    users = MobileUsers.objects.all()    

            else:
                filters = Q()

                if from_date and to_date:
                    filters &= Q(created_on__gte=from_date, created_on__lte=to_date+datetime.timedelta(days=1))

                if search:
                    filters &= Q(first_name__icontains=search) | Q(email__icontains=search)
                
                if status_ is None:
                    filters &= Q(is_active=1)
                else:
                    filters &= Q(is_active=status_)

                users = MobileUsers.objects.filter(filters)
                print(users, "here")

            pagination = UsersPagination()
            paginated_users = pagination.paginate_queryset(users, request)
            serializer = UsersListSerializer(paginated_users, many=True, context={"request": request})
            return pagination.get_paginated_response(serializer.data)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """
        Delete multiple users.
        """
        serializer = UsersMultipleDeleteSerializer(data=request.data)
        if serializer.is_valid():
        
            try:
                deleted_count = MobileUsers.objects.filter(id__in=serializer.validated_data["ids"], is_active=True).update(is_active=False)

                if deleted_count == 0:
                    return Response({"detail": "No users were deactivated"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{deleted_count} users deactivated successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UsersDetailView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]
    """
    Retrieve specific user
    """
    def get(self, request, pk):
        user = get_object_or_404(MobileUsers, id=pk)
        serializer = UsersRetrieveSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific user
        """

        user = get_object_or_404(MobileUsers, id=pk)

        serializer = UsersUpdateSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Profile updated successfully!!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        """
        Allow authenticated admin users to update user's profile picture.
        """

        user = get_object_or_404(MobileUsers, id=pk)

        serializer = UsersProfilePictureSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Profile picture updated successfully!!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Marks specific user as deactivated.
        """

        user = get_object_or_404(MobileUsers, id=pk, is_active=True)
        user.is_active=False
        user.save()

        return Response({"detail": "User marked as deactivated"}, status=status.HTTP_200_OK)
    

# TRASNACTIONS MODULE API'S
class TransactionListCreateUpdateView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def post(self, request):
        """
        To create new transaction.
        """

        serializer = TransactionsCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response({"detail": "Transaction created successfully!!"}, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """
        List all transactions.
        """

        serializer = TransactionsListCheckSerializer(data=request.query_params)
        if serializer.is_valid():

            type = serializer.validated_data.get("type", None)
            search = serializer.validated_data.get("search", None)
            from_date = serializer.validated_data.get("from_date", None)
            to_date = serializer.validated_data.get("to_date", None)
            if not from_date and not to_date and not type and not search:
                transactions = Transactions.objects.all()

            else:
                filters = Q()

                if from_date and to_date:
                    filters &= Q(created_on__gte=from_date, created_on__lte=to_date+datetime.timedelta(days=1))

                if type:
                    filters &= Q(type=type)

                if search:
                    filters &= Q(user_involved__icontains=search)

                transactions = Transactions.objects.filter(filters)

            pagination = TransactionsPagination()
            paginated_transactions = pagination.paginate_queryset(transactions, request)
            serializer = TransactionsListSerializer(paginated_transactions, many=True, context={"request": request})
            return pagination.get_paginated_response(serializer.data)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request):
        """
        To mark Pending status to Completed status 
        """

        serializer = TransactionsMarkAsCompletedSerializer(data=request.data)
        if serializer.is_valid():
            ids = request.data.get("ids")
            try:
                updated_count = Transactions.objects.filter(id__in=ids, status="pending").update(status="completed")

                if updated_count == 0:
                    return Response({"detail": "No transaction were updated"}, status=status.HTTP_404_NOT_FOUND)
                return Response({"detail": f"{updated_count} transactions updated successfully!!"}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

# DASHBOARD API'S *******
class KeyMatrixStatisticsView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get_last_updated_time(self, model):
        last_edited = model.objects.aggregate(last_edited=Max('last_edited'))['last_edited']
        if last_edited:
            return last_edited
        return None

    def get(self, request):
        """
        API endpoint to retrieve all the data needed for admin_dashboard's
        key matrix statistics.
        """

        total_professionals = Professionals.count()
        total_materials = Materials.count()
        total_registered_users = MobileUsers.count()
        total_transactions = Transactions.count()

        last_updated_professionals = self.get_last_updated_time(Professionals)
        last_updated_materials = self.get_last_updated_time(Materials)
        last_updated_users = self.get_last_updated_time(MobileUsers)
        last_updated_transactions = self.get_last_updated_time(Transactions)

        all_last_updated = [
            last_updated_professionals,
            last_updated_materials,
            last_updated_users,
            last_updated_transactions,
        ]
        most_recent_update = max(filter(None, all_last_updated))

        last_updated = f"Updated {timesince(most_recent_update)} ago" if most_recent_update else "No updates yet"

        response_data = {
            "total_professionals": total_professionals,
            "total_materials": total_materials,
            "total_registered_users": total_registered_users,
            "total_transactions": total_transactions,
            "last_updated": last_updated,
        }

        return Response(response_data, status=status.HTTP_200_OK)
    

class ProfessionalsGrowthChartView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):
        """
        Returns the count of professionals added each month 
        for the given number of past months.
        """

        serializer = ProfessionalsGrowthChartSerializer(data=request.query_params)
        if serializer.is_valid():
            months = serializer.validated_data["months"]
            end_date = datetime.datetime.now()

            # Initialize a dictionary to store counts for each month.
            month_counts = {}
            for i in range(months):
                month_start = datetime.datetime(end_date.year, end_date.month, 1)
                month_str = month_start.strftime("%Y-%m")
                # Initialize the count for this month to 0.
                month_counts[month_str] = 0
        
                end_date = month_start - datetime.timedelta(days=1)

            start_date = datetime.datetime(end_date.year, end_date.month, 1)
    
            professionals = Professionals.objects.filter(created_on__range=[start_date, datetime.datetime.now()])
            queryset = professionals.annotate(month=TruncMonth('created_on')).values('month').annotate(count=Count('id'))

            # Update the month_counts dictionary with actual counts from the query results.
            for entry in queryset:
                month_str = entry["month"].strftime("%Y-%m")
                month_counts[month_str] = entry["count"]

            professionals_growth_chart = [{'month': month, 'count': count} for month, count in month_counts.items()]

            response = {
                "months": months,
                "professionals_growth_chart": professionals_growth_chart
            }

            return Response(response, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RevenueGrowthView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):
        """
        Gives revenue growth report based on given periods,
        1. weekly -> gives report on that week
        2. monthly -> gives report on that month
        3. yearly -> gives report on that year
        """
        serializer = RevenueGrowthSerializer(data=request.query_params)
        if serializer.is_valid():
            periods = serializer.validated_data['periods']
            
            if periods == 'weekly':
                today = datetime.datetime.now()
                start_date = datetime.datetime(today.year, today.month, today.day) - datetime.timedelta(days=datetime.datetime.now().weekday())
                end_date = start_date + datetime.timedelta(days=6)

                # Get previous week date to calculate percentage
                prev_start_date = start_date - datetime.timedelta(days=7)
                delta = datetime.timedelta(days=1)

                transactions = Transactions.objects.filter(created_on__gte=start_date, type='payment', status='completed')
                total_revenue = transactions.aggregate(Sum('amount'))['amount__sum'] or 0.0

                prev_transactions = Transactions.objects.filter(created_on__gte=prev_start_date, created_on__lt=start_date, status='completed')
                prev_total_revenue = prev_transactions.aggregate(Sum('amount'))['amount__sum'] or 0.0

                if prev_total_revenue == 0:
                    percentage_change = 100.0 if total_revenue > 0 else 0.0
                else:
                    percentage_change = ((total_revenue - prev_total_revenue) / prev_total_revenue) * 100

                current_date = start_date
                revenue_data = []
                while current_date <= end_date:
                    next_date = current_date + delta
                    period_revenue = transactions.filter(created_on__gte=current_date, created_on__lt=next_date).aggregate(Sum('amount'))['amount__sum'] or 0.0
                    revenue_data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'revenue': period_revenue
                    })

                    current_date = next_date

            
            elif periods == 'monthly':
                today = datetime.datetime.now()
                start_date = datetime.datetime(today.year, today.month, 1)
                # Get the current month's last date
                if today.month == 12:
                    end_date = datetime.datetime(today.year+1, 1, 1) - datetime.timedelta(days=1)
                else:
                    end_date = datetime.datetime(today.year, today.month+1, 1) - datetime.timedelta(days=1)
                # Get previous week to calculate percentage
                if today.month == 1:
                    prev_start_date = datetime.datetime(today.year-1, 12, 1)
                else:
                    prev_start_date = datetime.datetime(today.year, today.month-1, 1)
                delta = datetime.timedelta(days=7)


                transactions = Transactions.objects.filter(created_on__gte=start_date, type='payment', status='completed')
                total_revenue = transactions.aggregate(Sum('amount'))['amount__sum'] or 0.0

                prev_transactions = Transactions.objects.filter(created_on__gte=prev_start_date, created_on__lt=start_date, status='completed')
                prev_total_revenue = prev_transactions.aggregate(Sum('amount'))['amount__sum'] or 0.0

                if prev_total_revenue == 0:
                    percentage_change = 100.0 if total_revenue > 0 else 0.0
                else:
                    percentage_change = ((total_revenue - prev_total_revenue) / prev_total_revenue) * 100

                current_date = start_date
                revenue_data = []
                while current_date <= end_date:
                    next_date = current_date + delta
                    period_revenue = transactions.filter(created_on__gte=current_date, created_on__lt=next_date).aggregate(Sum('amount'))['amount__sum'] or 0.0
                    revenue_data.append({
                        'week_start': current_date.strftime('%Y-%m-%d'),
                        'week_end': (next_date-datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                        'revenue': period_revenue
                    })
                    current_date = next_date
    
            elif periods == 'yearly':
                today = datetime.datetime.now()
                start_date = datetime.datetime(today.year, 1, 1)
                end_date = datetime.datetime(today.year, 12, 31)
                prev_start_date = datetime.datetime(today.year-1, 1, 1)

                transactions = Transactions.objects.filter(created_on__gte=start_date, type='payment', status='completed')
                total_revenue = transactions.aggregate(Sum('amount'))['amount__sum'] or 0.0

                prev_transactions = Transactions.objects.filter(created_on__gte=prev_start_date, created_on__lt=start_date, type='payment', status='completed')
                prev_total_revenue = prev_transactions.aggregate(Sum('amount'))['amount__sum'] or 0.0

                if prev_total_revenue == 0:
                    percentage_change = 100.0 if total_revenue > 0 else 0.0
                else:
                    percentage_change = ((total_revenue - prev_total_revenue) / prev_total_revenue) * 100

                current_date = start_date
                revenue_data = []
                while current_date <= end_date:
                    # Get next month's first date
                    if current_date.month == 12:
                        next_date = datetime.datetime(current_date.year+1, 1, 1)
                    else:
                        next_date = datetime.datetime(current_date.year, current_date.month+1, 1)

                    period_revenue = transactions.filter(created_on__gte=current_date, created_on__lt=next_date).aggregate(Sum('amount'))['amount__sum'] or 0.0
                    revenue_data.append({
                        'month': current_date.strftime('%Y-%m'),
                        'revenue': period_revenue
                    })
                    current_date = next_date
    
            data = {
                'periods': periods,
                'total_revenue': total_revenue,
                'percentage_change': percentage_change,
                'revenue_data': revenue_data,
            }
            return Response(data, status=status.HTTP_200_OK)
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ActivityTimelineView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):

        type = request.query_params.get("type")
        if not type or type not in ["professionals", "materials", "events", "books", "notifications", "transactions", "users"]:
            return Response({"detail": "type is required and should be either one of these options: [professionals, materials, events, books, notifications, transactions, users]"})
        
        if type == "professionals":
            professionals = Professionals.objects.all().order_by('-created_on')[:10]
            serializer = ProfessionalsActivitySerializer(professionals, many=True, context={"request": request})

        elif type == "materials":
            materials = Materials.objects.all().order_by('-created_on')[:10]
            serializer = MaterialsActivitySerializer(materials, many=True, context={"request": request})
            
        elif type == "events":
            events = Events.objects.all().order_by('-created_on')[:10]
            serializer = EventsActivitySerializer(events, many=True, context={"request": request})

        elif type == "books":
            books = Books.objects.all().order_by('-created_on')[:10]
            serializer = BooksActivitySerializer(books, many=True, context={"request": request})

        elif type == "notifications":
            notifications = Notifications.objects.all().order_by('-created_on')[:10]
            serializer = NotificationsActivitySerializer(notifications, many=True, context={"request": request})

        elif type == "transactions":
            transactions = Transactions.objects.all().order_by('-created_on')[:10]
            serializer = TransactionsActivitySerializer(transactions, many=True, context={"request": request})

        else:
            users = MobileUsers.objects.all().order_by('-created_on')[:10]
            serializer = MobileUsersActivitySerializer(users, many=True, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class MaterialsDistributionView(APIView):
    """
    API endpoint that returns the distribution of materials by type.
    
    This endpoint calculates the percentage distribution of different types of materials
    (Electricals, Building Materials, Others).
    """

    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):
        total_count = Materials.objects.count()
        electricals_count = Materials.objects.filter(type='Electricals').count()
        building_materials_count = Materials.objects.filter(type='Building Materials').count()
        others_count = total_count - (electricals_count + building_materials_count)

        if total_count > 0:
            electricals_percentage = (electricals_count / total_count) * 100
            building_materials_percentage = (building_materials_count / total_count) * 100
            others_percentage = (others_count / total_count) * 100
        else:
            electricals_percentage = 0
            building_materials_percentage = 0
            others_percentage = 0

        data = {
            'total_count': total_count,
            'electricals_count': electricals_count,
            'electricals_percentage': electricals_percentage,
            'building_materials_count': building_materials_count,
            'building_materials_percentage': building_materials_percentage,
            'others_count': others_count,
            'others_percentage': others_percentage
        }

        return Response(data, status=status.HTTP_200_OK)
    

# NOTIFICATIONS MODULE APIS *******
class NotificationsFCMHTTPListCreateView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request):
        """
        List all notifications
        """

        serializer = NotificationsListCheckSerializer(data=request.query_params)
        if serializer.is_valid():

            recipient = serializer.validated_data.get("status", None)
            search = serializer.validated_data.get("search", None)
            from_date = serializer.validated_data.get("from_date", None)
            to_date = serializer.validated_data.get("to_date", None)

            if not from_date and not to_date and not recipient and not search:
                notifications = Notifications.objects.all()

            else:
                filters = Q()

                if from_date and to_date:
                    filters &= Q(created_on__gte=from_date, created_on__lte=to_date+datetime.timedelta(days=1))

                if recipient:
                    filters &= Q(recipient=recipient)

                if search:
                    filters &= Q(title__icontains=search) | Q(body__icontains=search)

                notifications = Notifications.objects.filter(filters)

            pagination = NotificationsPagination()
            paginated_notifications = pagination.paginate_queryset(notifications, request)
            serializer = NotificationsListSerializer(paginated_notifications, many=True, context={"request": request})
            return pagination.get_paginated_response(serializer.data)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        This API sends push notifications to users with an FCM token if the status is 'sent'. 
        If the status is 'pending', it adds the notification to the Notifications table for later sending.
        """

        serializer = NotificationsCreateSerializer(data=request.data)
        if serializer.is_valid():

            if serializer.validated_data["status"] != "pending":

                title = serializer.validated_data['title']
                body = serializer.validated_data['body']
                recipient = serializer.validated_data['recipient']

                recipient_tokens = get_recipient_fcm_tokens(recipient)

                if recipient_tokens:
                    """
                    We need to send the image url to firebase
                    so we are saving notifaction first before
                    sending it.
                    """
                    notification = serializer.save()
                    image = request.build_absolute_uri(notification.image.url)

                    detail = send_fcm_notification(recipient_tokens, title, body, image)

                    if detail["sent_count"] == 0:

                        notification.status = "failed"
                        notification.save()

                        return Response({"detail": detail["response"].json()}, status=detail["response"].status_code)
                    
                    detail.pop("response")
                    return Response({"detail": "Notification sent successfully!", "data": detail}, status=status.HTTP_200_OK)
                    
                return Response({"detail": "No user found; notification cannot be sent"}, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response({"detail": "Notification added successfully"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class NotificationsFCMHTTPRetrieveUpdateDeleteView(APIView):
    permission_classes = [IsAuthenticatedAndAdmin]

    def get(self, request, pk):
        """
        List specific notification.
        """

        notification = get_object_or_404(Notifications, id=pk)
        serializer = NotificationsRetrieveUpdateSerializer(notification)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        """
        Update specific notification.
        """

        notification = get_object_or_404(Notifications, id=pk)

        serializer = NotificationsRetrieveUpdateSerializer(notification, data=request.data)
        if serializer.is_valid():

            if serializer.validated_data["status"] == "sent":

                title = serializer.validated_data['title']
                body = serializer.validated_data['body']
                recipient = serializer.validated_data['recipient']

                recipient_tokens = get_recipient_fcm_tokens(recipient)
                if recipient_tokens:
                    image = request.build_absolute_uri(notification.image.url)
                    detail = send_fcm_notification(recipient_tokens, title, body, image)

                    if detail["sent_count"] == 0:

                        serializer.validated_data["status"] = "failed"
                        serializer.save()

                        return Response({"detail": detail["response"].json()}, status=detail["response"].status_code)
                    
                    detail.pop("response")
                    serializer.save()
                    return Response({"detail": "Notification sent successfully!", "data": detail}, status=status.HTTP_200_OK)
                    
                serializer.save()
                return Response({"detail": "Notification updated sucessfully but no users found"}, status=status.HTTP_200_OK)

            serializer.save()
            return Response({"detail": "Notification updated successfully!"}, status=status.HTTP_200_OK)
        
        return Response({"detail": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        """
        Delete specific material.
        """

        notification = get_object_or_404(Notifications, id=pk)
        try:
            notification.delete()
            return Response({"detail": "Notification deleted successfully!!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)