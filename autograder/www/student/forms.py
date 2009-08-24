import django.forms as forms



class SubmitAssignmentForm(forms.Form):
    #which file to grade
  assignment_id = forms.IntegerField()

