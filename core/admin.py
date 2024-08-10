from django.contrib import admin

# Local imports
from core.models import Addresses, BooksReview, CustomUser, AdminUsers, MaterialsReview, MobileUsers, Portfolios, Professionals, Books, Materials, Notifications, Events, ProReview, Referrals, Transactions

# Register your models here.
admin.site.register(AdminUsers)
admin.site.register(MobileUsers)
admin.site.register(Professionals)
admin.site.register(Books)
admin.site.register(Materials)
admin.site.register(Notifications)
admin.site.register(Events)
admin.site.register(ProReview)
admin.site.register(Transactions)
admin.site.register(Referrals)
admin.site.register(Portfolios)
admin.site.register(BooksReview)
admin.site.register(MaterialsReview)
admin.site.register(Addresses)