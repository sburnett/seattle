from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

#types of account
USER_CHOICES = (
    ('student', 'student'),
    ('instructor', 'instructor'),
)




#extends the User class to add university_id and is_student fields
class user_profile(models.Model):
    user = models.ForeignKey(User, unique=True)
    user_type = models.CharField(max_length=128, choices=USER_CHOICES)
    is_validated = models.BooleanField()
    affiliation = models.CharField(max_length=128, null=True)
    course_id = models.IntegerField(null=True)




class pending_validations(models.Model):
    user = models.ForeignKey(User, unique=True)
    website = models.CharField(max_length=128)



#creates a callback so that whenever a new User is created or saved
#a profile will also be created for them if it doesn't exist
def user_profile_callback(sender, instance, **kwargs):
    profile, new = user_profile.objects.get_or_create(user=instance)
    

post_save.connect(user_profile_callback, sender = User)
