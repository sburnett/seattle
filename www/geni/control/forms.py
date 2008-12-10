"""
<Program Name>
  forms.py

<Started>
  October, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Provides a variety of form objects used in geni.

  This file defines various forms used by the geni website. These form
  classes have functions to perform specific field validation, and to
  perform other operations on form fields.

  See http://docs.djangoproject.com/en/dev/topics/forms/?from=olddocs
"""

import django.forms as forms
from django.contrib.auth.models import User as djUser
from models import User,Donation,Vessel,VesselMap,Share

# TODO: make pub-key into a custom class
# class PubKeyField(forms.FileField):
#     def clean(self,value,initial):
#         forms.FileField.clean(self,value,initial)
#         if value == "":
#             return ""
#         if value.size > 2048:
#             raise forms.ValidationError, "Public key too large, file size limit is 2048 bytes"
#         pubkey = f.read()
#         # TODO: validate public key as a valid Seattle key
#         return pubkey

def gen_get_form(geni_user,req_post=None):
    """
    <Purpose>
        Dynamically generates a GetVesselsForm that has the right
        number vessels (the allowed number of vessels a user may
        acquire). Possibly generate a GetVesselsForm from an HTTP POST
        request.

    <Arguments>
        geni_user:
            geni_user object
        req_post:
            An HTTP POST request (django) object from which a
            GetVesselsForm may be instantiated. If this argument is
            not supplied, a blank form will be created

    <Exceptions>
        None?

    <Side Effects>
        None.

    <Returns>
        A GetVesselsForm object that is instantiated with a req_post
        (if given). None is returned if the user cannot acquire any
        more vessels.
    """
    
    # max allowed resources this user may get
    donations = Donation.objects.filter(user=geni_user).filter(active=1)
    num_donations = len(donations)
    max_num = 10 * (num_donations + 1)
    
    # number of vessels already used by this user
    myvessels = VesselMap.objects.filter(user = geni_user)
    
    if len(myvessels) > max_num:
        max_num = 0
    else:
        max_num = max_num - len(myvessels)

    if max_num == 0:
        return None

    # the total number of vessels a user may acquire
    get_vessel_choices = zip(range(1,max_num+1),range(1,max_num+1))

    class GetVesselsForm(forms.Form):
        """
        <Purpose>
            Customized admin view of the User model
        <Side Effects>
            None
        <Example Use>
            Used internally by django
        """
        num = forms.ChoiceField(choices=get_vessel_choices)
        env = forms.ChoiceField(choices=((1,'LAN'),(2,'WAN'),(3,'Random')))
        
    if req_post is None:
        return GetVesselsForm()
    return GetVesselsForm(req_post)


class AddShareForm(forms.Form):
    """
    <Purpose>
      A form to add a share between two users

    <Side Effects>
      None
      
    <Example Use>
      **********
    """
    
    username = forms.CharField(max_length=32,min_length=3,error_messages={'required': 'Please enter a username'})
    percent = forms.DecimalField(min_value=1,max_value=100,error_messages={'required': 'Please enter a percentage'})

    def clean_username(self):
        """
        <Purpose>

        
        <Arguments>
        
        <Exceptions>

        <Side Effects>
        
        <Returns>
        
        """

        value = self.cleaned_data['username']
        try:
            wuser = djUser.objects.get(username=value)
        except:
            raise forms.ValidationError, "Username does not exist"
        try:
            to_guser = User.objects.get(www_user=wuser)
        except:
            raise forms.ValidationError, "Username invalid -- inconsistency between auth and geni user records"
        if to_guser == self.guser:
            raise forms.ValidationError, "Cannot share with yourself"
        if len(Share.objects.filter(from_user=self.guser,to_user=to_guser)) != 0:
            raise forms.ValidationError, "For users you already share with, update the table above"
        return to_guser

    def set_user(self,user):
        """
        <Purpose>

        
        <Arguments>
        
        <Exceptions>

        <Side Effects>
        
        <Returns>
        
        """

        self.guser = user

    def clean_percent(self):
        """
        <Purpose>

        
        <Arguments>
        
        <Exceptions>

        <Side Effects>
        
        <Returns>
        
        """

        value = self.cleaned_data['percent']
        shares = Share.objects.filter(from_user = self.guser)
        sum = 0
        for s in shares:
            sum+=s.percent
        if sum > 100:
            raise forms.ValidationError, "DB inconsistent - you have more than 100% shared"
        if sum+value > 100:
            raise forms.ValidationError, "You cannot share more than a total of 100%"
        return value
