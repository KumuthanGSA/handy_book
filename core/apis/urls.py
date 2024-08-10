from django.urls import path

# Third part imports
from rest_framework_simplejwt.views import TokenRefreshView

# Local imports
from core.apis.admin_dashboard_apis import ActivityTimelineView, AdminLoginView, AdminLogoutView, AdminAccountSettingsView, AdminSecurityView, BooksDetailedRetrieveView, BooksListCreateDeleteView, BooksRetriveUpdateDeleteView, EventsListCreateDeleteView, EventsRetriveUpdateDeleteView, KeyMatrixStatisticsView, ListExpertiseView, LocationListView, MaterialsDetailedView, MaterialsDistributionView, MaterialsListCreateDeleteView, MaterialsRetriveUpdateDeleteView, MaterialsSupplierListView, MaterialsTypeListView, NotificationsFCMHTTPListCreateView, NotificationsFCMHTTPRetrieveUpdateDeleteView, PortfoliosImagesDeleteView, ProfessionalsDetailView, ProfessionalsGrowthChartView, ProfessionalsListCreateDeleteView, ProfessionalsPortfoliosCreateListUpdateDeleteView, ProfessionalsRetrieveUpdateDeleteView, RevenueGrowthView, TransactionListCreateUpdateView, UsersDetailView, UsersListDeleteView

urlpatterns = [
    # Admin management
    path('login', AdminLoginView.as_view()),
    path('refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout', AdminLogoutView.as_view()),

    # Admin dashboard
    path('dashboard/key_matrix_statistics', KeyMatrixStatisticsView.as_view()),
    path('dashboard/professionals_growth_chart', ProfessionalsGrowthChartView.as_view()),
    path('dashboard/revenue_growth_chart', RevenueGrowthView.as_view()),
    path('dashboard/activity_timeline', ActivityTimelineView.as_view()),
    path('dashboard/materials_distribution', MaterialsDistributionView.as_view()),

    # Settings
    path('account_settings', AdminAccountSettingsView.as_view()),
    path('change_password', AdminSecurityView.as_view()),

    # Professionals
    path('professionals', ProfessionalsListCreateDeleteView.as_view()),
    path('professionals/<int:pk>', ProfessionalsRetrieveUpdateDeleteView.as_view()),
    path('professionals/details/<int:pk>', ProfessionalsDetailView.as_view()),
    path('professionals/portfolios/<int:pk>', ProfessionalsPortfoliosCreateListUpdateDeleteView.as_view()),
    path('professionals/portfolios/images/<int:pk>', PortfoliosImagesDeleteView.as_view()),
    path('professionals/expertise', ListExpertiseView.as_view()),
    path('professionals/locations', LocationListView.as_view()),
    

    #Users
    path('users', UsersListDeleteView.as_view()),
    path('users/<int:pk>', UsersDetailView.as_view()),

    # Books
    path('books', BooksListCreateDeleteView.as_view()),
    path('books/<int:pk>', BooksRetriveUpdateDeleteView.as_view()),
    path('books/details/<int:pk>', BooksDetailedRetrieveView.as_view()),

    # Materials
    path('materials', MaterialsListCreateDeleteView.as_view()),
    path('materials/<int:pk>', MaterialsRetriveUpdateDeleteView.as_view()),
    path('materials/details/<int:pk>', MaterialsDetailedView.as_view()),
    path('materials/type', MaterialsTypeListView.as_view()),
    path('materials/supplier', MaterialsSupplierListView.as_view()),

    # Events
    path('events', EventsListCreateDeleteView.as_view()),
    path('events/<int:pk>', EventsRetriveUpdateDeleteView.as_view()),

    # Transactions
    path('transactions', TransactionListCreateUpdateView.as_view()),

    # Notifications
    path('notifications', NotificationsFCMHTTPListCreateView.as_view()),
    path('notifications/<int:pk>', NotificationsFCMHTTPRetrieveUpdateDeleteView.as_view()),
]