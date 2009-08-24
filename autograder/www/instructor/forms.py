from django import forms
from instructor.widgets import DateTimeWidget
import datetime	


class DateTimeForm(forms.Form):
    #time = forms.DateTimeField(initial=datetime.date.today, label='Starting On', widget=DateTimeWidget)
    due_date = forms.DateTimeField(label='due date' , initial='Y-m-d H:M:S', widget=DateTimeWidget)
    #due_date = forms.DateTimeField(initial=datetime.date.today, label='Due Date', widget=DateTimeWidget)


class GradeAssignmentsForm(forms.Form):
    #which file to grade
  assignment_id = forms.IntegerField()

class SubmitAssignmentForm(forms.Form):
    #which file to grade
  submission_id = forms.IntegerField()
