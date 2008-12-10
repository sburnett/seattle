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
            Generates a form to acquire vessels by the user
        <Side Effects>
            None
        <Example Use>
            GetVesselsForm()
                to generate a blank form
            GetVesselsForm(post_request)
                to generate a form from an existing POST request
        """
        # maximum number of vessels a user is allowed to acquire
        num = forms.ChoiceField(choices=get_vessel_choices)

        # the various environmen types the user may select from
        env = forms.ChoiceField(choices=((1,'LAN'),(2,'WAN'),(3,'Random')))
        
    if req_post is None:
        return GetVesselsForm()
    return GetVesselsForm(req_post)


class AddShareForm(forms.Form):
    """
    <Purpose>
        A form to add a new Share between two users. Note that this
        form cannot be used to update an existing Share record

    <Side Effects>
        None
      
    <Example Use>
        AddShareForm()
           To generate a blank form
        AddShareForm(post_request)
            To generate a form from an existing POST request object
    """

    # username of the user who the sharing is with
    username = forms.CharField(max_length=32,min_length=3,error_messages={'required': 'Please enter a username'})

    # the percentage of resources to share with the user
    percent = forms.DecimalField(min_value=1,max_value=100,error_messages={'required': 'Please enter a percentage'})

    def clean_username(self):
        """
        <Purpose>
            Verifies user input as being a valid GENI username.
            
        <Arguments>
            None.
            
        <Exceptions>
            forms.ValidationError
                When the user attempts to share with themselves
                When a username does not exist
                When username is invalid (inconsistent DB)
                When the user is already being shared with
            
        <Side Effects>
            None.
            
        <Returns>
            A valid GENI username _to_ whom the share is intended

        <Note>
            This function is used internally by django. It is called
            when django is verifying each of the form fields

        <ToDo>
            Come up with sensical Exception classes
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
            Used to specify the user from whom the resources are being shared
        
        <Arguments>
            user:
                geni user object representing the sharing user
                
        <Exceptions>
            None
            
        <Side Effects>
            None
            
        <Returns>
            None
        """
        self.guser = user
        return


    def clean_percent(self):
        """
        <Purpose>
            Verifies a user-supplied percentage value for the
            percentage of resources to share
        
        <Arguments>
            None
        
        <Exceptions>
            forms.ValidationError
                When DB is inconsistent (user has more than 100% shared)
                When user attempts to share more than 100%

        <Side Effects>
            None
            
        <Returns>
            The verified, or 'cleaned' percentage value

        <Note>
            This function is used internally by django. It is called
            when django is verifying each of the form fields
            
        <ToDo>
            Come up with sensical Exception classes
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
