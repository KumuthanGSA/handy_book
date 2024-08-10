from rest_framework.pagination import PageNumberPagination

# Create your paginators here

# PROFESSIONALS MODULE PAGINATIONS
class ProfessionalsPagination(PageNumberPagination):
    page_size = 10


# BOOKS MODULE PAGINATIONS *******
class BooksPagination(PageNumberPagination):
    page_size = 10


# EVENTS MODULE PAGINATIONS *******
class EventsPagination(PageNumberPagination):
    page_size = 10


# MATERIALS MODULE PAGINATIONS *******
class MaterialsPagination(PageNumberPagination):
    page_size = 10


# USERS MODULE PAGINATIONS *******
class UsersPagination(PageNumberPagination):
    page_size = 10


# TRANSACTIONS MODULE PAGINATIONS *******
class TransactionsPagination(PageNumberPagination):
    page_size = 10


# NOTIFICATION MODULE PAGINATIONS *******
class NotificationsPagination(PageNumberPagination):
    page_size = 10