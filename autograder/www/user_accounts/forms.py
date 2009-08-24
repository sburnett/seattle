#from django.core.validators import alnum_re
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
#from registration.models import RegistrationProfile
from user_accounts.models import *
from django import forms
import re




class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.
   
    Validates that the requested username and email are not already in use, and
    requires the password to be entered twice to catch typos.
   
    Subclasses should feel free to add any additional validation they
    need, but should either preserve the base ``save()`` or implement
    a ``save()`` which accepts the ``profile_callback`` keyword
    argument and passes it through to
    ``RegistrationProfile.objects.create_inactive_user()``.
   
    """
    username = forms.CharField(label='Username')
    first_name = forms.CharField(label='First name')
    last_name = forms.CharField(label='Last name')
    email = forms.EmailField(label='Email Address')
    password1 = forms.CharField(max_length=100, label='Password', help_text='100 characters max.')
    password2 = forms.CharField(max_length=100, label='Retype password')



    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
       
        """
        alphanum_re = re.compile(r'^\w+$')
        if not alphanum_re.search(self.cleaned_data['username']):
            raise forms.ValidationError(_(u'Usernames can only contain letters, numbers and underscores'))
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError(_(u'This username is already taken. Please choose another.'))


    def clean_name(self):
        if not str(self.cleaned_data['first_name']).isalpha():
            raise forms.ValidationError(_(u'First name can only contain letters'))
        if not str(self.cleaned_data['last_name']).isalpha():
            raise forms.ValidationError(_(u'Last name can only contain letters'))


    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
       
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_(u'You must type the same password each time'))
        return self.cleaned_data







class InstructorRegistrationForm(RegistrationForm):
    """
       Form for registering instructors inherited from RegistrationFrom
    """
    affiliation = forms.CharField(label='Affiliation') 


   
    def save(self, profile_callback=None):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User``.
       
        This is essentially a light wrapper around
        ``RegistrationProfile.objects.create_inactive_user()``,
        feeding it the form data and a profile callback (see the
        documentation on ``create_inactive_user()`` for details) if
        supplied.
       
        """
                                                                   # profile_callback=profile_callback)
        new_user = User.objects.create_user(self.cleaned_data['username'], self.cleaned_data['email'], self.cleaned_data['password1'])
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_user.save()
        
        new_user_profile = user_profile.objects.get(user=new_user)
        new_user_profile.user_type = 'instructor'
        new_user_profile.affiliation = self.cleaned_data['affiliation']
        new_user_profile.is_validated = 'False'
        new_user_profile.save()        
        return new_user



class StudentRegistrationForm(RegistrationForm):
    instructor_name = forms.CharField(label='Instructor Last Name')
    course_id = forms.IntegerField(label='Course Code')


    def save(self, profile_callback=None):
        """
        Create the new ``User`` and ``RegistrationProfile``, and
        returns the ``User``.
       
        This is essentially a light wrapper around
        ``RegistrationProfile.objects.create_inactive_user()``,
        feeding it the form data and a profile callback (see the
        documentation on ``create_inactive_user()`` for details) if
        supplied.
       
        """
                                                                   
        new_user = User.objects.create_user(self.cleaned_data['username'], self.cleaned_data['email'], self.cleaned_data['password1'])
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']
        new_user.save()
        
        new_user_profile = user_profile.objects.get(user=new_user)
        new_user_profile.user_type = 'student'
        new_user_profile.course_id = self.cleaned_data['course_id']
        new_user_profile.is_validated = 'False'
        new_user_profile.save()        
        return new_user

