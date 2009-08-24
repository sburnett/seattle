from django.db import models
from django.contrib.auth.models import User


class courses(models.Model):
    instructor = models.ForeignKey(User)
    course_name = models.CharField(max_length=128)




    
class course_roster(models.Model):
    student = models.ForeignKey(User)
    course = models.ForeignKey(courses)





class project_description(models.Model):
    name = models.CharField(max_length=128, unique=True)
    sharable = models.BooleanField()
    description = models.CharField(max_length=1024)
    test_code_filename = models.CharField(max_length=128)
    created_by = models.ForeignKey(User)
    
    

class assignment(models.Model):
    course = models.ForeignKey(courses)
    project = models.ForeignKey(project_description)
    #student_results_viewable = models.BooleanField()
    assignment_name = models.CharField(max_length=128)
    due_date = models.DateTimeField()





class student_submission(models.Model):
    student = models.ForeignKey(User)
    assignment = models.ForeignKey(assignment)
    student_code_filename = models.CharField(max_length=128)
    time = models.DateTimeField()
    grade_results = models.CharField(max_length=1024)


class submissions_to_grade(models.Model):
    submission = models.ForeignKey(student_submission)
