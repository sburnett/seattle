import django.forms as forms
from django.contrib.auth.models import User as djUser
from models import User,Donation,Vessel,VesselMap,Share

class AffiliationField(forms.Field):
    def clean(self,value):
        if value == "":
            raise forms.ValidationError, "Affiliation cannot be blank"
        return value

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

class AddShareForm(forms.Form):
    username = forms.CharField(max_length=32,min_length=3,error_messages={'required': 'Please enter a username'})
    percent = forms.DecimalField(min_value=1,max_value=100,error_messages={'required': 'Please enter a percentage'})

    def clean_username(self):
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
        return to_guser

    def set_user(self,user):
        self.guser = user

    def clean_percent(self):
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
