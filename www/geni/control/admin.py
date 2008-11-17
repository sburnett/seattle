from geni.control.models import User, Donation, Vessel, VesselPorts, VesselMap, Share
from django.contrib import admin

class UserAdmin(admin.ModelAdmin):
    list_display = ('www_user', 'port', 'affiliation')
    list_filter = ('affiliation', 'port')
    #search_fields = ['www_user','affiliation']

class DonationAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip', 'port', 'date_added', 'last_heard', 'status', 'version')
    list_filter = ('user', 'status', 'version')
    #search_fields = ['user.www_user.username','ip']

class ShareAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'percent')
    list_filter = ('from_user', 'to_user')
    #search_fields = ['from_user','to_user']
    
class VesselAdmin(admin.ModelAdmin):
    list_display = ('donation', 'name', 'status', 'extra_vessel')
    list_filter = ('donation', 'status', 'extra_vessel')

class VesselMapAdmin(admin.ModelAdmin):
    list_display = ('vessel', 'user', 'expiration')
    list_filter = ('user',)

class VesselPortsAdmin(admin.ModelAdmin):
    list_display = ('vessel', 'port')
    list_filter = ('port',)

admin.site.register(Donation, DonationAdmin)
admin.site.register(Share, ShareAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(VesselMap, VesselMapAdmin)
admin.site.register(VesselPorts, VesselPortsAdmin)
admin.site.register(Vessel, VesselAdmin)



