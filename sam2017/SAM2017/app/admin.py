from django.contrib import admin
from .models import Paper, SAM2017User, PCMAssign, PCMPickList,Notification, UserNotification, PCMReview, PCCReview, Deadline, NotificationTemplate
from django.contrib.auth.models import User

# Register your models here.
admin.site.register(Paper)
admin.site.register(SAM2017User)
admin.site.register(PCMPickList)
admin.site.register(PCMAssign)
admin.site.register(Notification)
admin.site.register(UserNotification)
admin.site.register(PCMReview)
admin.site.register(PCCReview)
admin.site.register(Deadline)
admin.site.register(NotificationTemplate)

