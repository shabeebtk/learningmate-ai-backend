from django.contrib import admin
from accounts.models import MyUsers, UserProfile
# Register your models here.


admin.site.register(MyUsers)
admin.site.register(UserProfile)