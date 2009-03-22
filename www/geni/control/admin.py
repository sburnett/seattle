"""
<Program Name>
  admin.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Provides a geni admin interface to the control application

  This file customizes numerous views of database models relevant to
  GENI. This file will expand as the admin interface requires more
  functionality.

  See http://docs.djangoproject.com/en/dev/ref/contrib/admin/
"""

from geni.control.models import User, Donation, Vessel, VesselPort, VesselMap, Share
from django.contrib import admin

class UserAdmin(admin.ModelAdmin):
    """
    <Purpose>
      Customized admin view of the User model
    <Side Effects>
      None
    <Example Use>
      Used internally by django
    """

    list_display = ('www_user', 'port', 'affiliation')
    list_filter = ('affiliation', 'port')
    #search_fields = ['www_user','affiliation']

class DonationAdmin(admin.ModelAdmin):
    """
    <Purpose>
      Customized admin view of the Donation model
    <Side Effects>
      None
    <Example Use>
      Used internally by django
    """
    
    list_display = ('user', 'ip', 'port', 'date_added', 'last_heard', 'status', 'version')
    list_filter = ('user', 'status', 'version')
    #search_fields = ['user.www_user.username','ip']

class ShareAdmin(admin.ModelAdmin):
    """
    <Purpose>
      Customized admin view of the Share model
    <Side Effects>
      None
    <Example Use>
      Used internally by django
    """
        
    list_display = ('from_user', 'to_user', 'percent')
    list_filter = ('from_user', 'to_user')
    #search_fields = ['from_user','to_user']
    
class VesselAdmin(admin.ModelAdmin):
    """
    <Purpose>
      Customized admin view of the Vessel model
    <Side Effects>
      None
    <Example Use>
      Used internally by django
    """
        
    list_display = ('donation', 'name', 'status', 'extra_vessel', 'assigned')
    list_filter = ('donation', 'status', 'extra_vessel', 'assigned')

class VesselMapAdmin(admin.ModelAdmin):
    """
    <Purpose>
      Customized admin view of the VesselMap model
    <Side Effects>
      None
    <Example Use>
      Used internally by django
    """

    list_display = ('vessel_port', 'user', 'expiration')
    list_filter = ('user',)

class VesselPortAdmin(admin.ModelAdmin):
    """
    <Purpose>
      Customized admin view of the VesselPort model
    <Side Effects>
      None
    <Example Use>
      Used internally by django
    """

    list_display = ('vessel', 'port')
    list_filter = ('port',)

# register/associate each custom admin view defined above with the
# model defined in geni.control.models
admin.site.register(Donation, DonationAdmin)
admin.site.register(Share, ShareAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(VesselMap, VesselMapAdmin)
admin.site.register(VesselPort, VesselPortAdmin)
admin.site.register(Vessel, VesselAdmin)



