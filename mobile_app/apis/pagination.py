from rest_framework.pagination import PageNumberPagination

# Create your paginators here

# PROFESSIONALS MODULE PAGINATIONS
class ProfessionalsPagination(PageNumberPagination):
    page_size = 15


# MATERIALS MODULE PAGINATIONS *******
class MaterialsPagination(PageNumberPagination):
    page_size = 15


# BOOKS MODULE PAGINATIONS *******
class BooksPagination(PageNumberPagination):
    page_size = 15

# FAVORITES MODULE PAGINATIONS *******
class FavoritesPagination(PageNumberPagination):
    page_size = 15

# FAVORITES MODULE PAGINATIONS *******
class TopBrandsPafination(PageNumberPagination):
    page_size = 15