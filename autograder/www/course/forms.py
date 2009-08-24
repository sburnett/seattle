from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from user_accounts.models import *
from django import forms
import re

class UploadProjectForm(forms.Form):
    name = forms.CharField(max_length=128,label='Project title')
    description = forms.CharField(widget=forms.Textarea)
    sharable = forms.BooleanField(required=False, label='Share this project with other instructors')
    test_code = forms.FileField()

class UploadAssignmentForm(forms.Form):
    assignment_code = forms.FileField()


