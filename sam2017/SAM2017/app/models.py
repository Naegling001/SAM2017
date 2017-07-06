from django.db import models
from django import forms
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator


class SAM2017User(models.Model):
    user = models.OneToOneField(User)

    # first_name = models.CharField(max_length=30, blank=False)
    # last_name = models.CharField(max_length=30, blank=False)
    # email = models.EmailField()
    # password = models.CharField(max_length=50)
    # username = models.CharField(max_length=30, blank=False)
    # type = models.CharField(max_length=10, choices=USER_TYPE, default=AUTHOR)

    class Meta:
        app_label = 'app'

    def __str__(self):
        return self.user.username

class Paper(models.Model):
    title = models.CharField(max_length = 255)
    revision = models.BooleanField()
    date_submitted = models.DateTimeField(auto_now=True, null=True)
    contact_author = models.ForeignKey(SAM2017User, related_name="submitter")
    authors = models.CharField(max_length = 255)
    deadline = models.DateTimeField(null=True)
    docfile = models.FileField(upload_to='documents/%y/%m/%d')

    MLA = "MLA"
    APA = "APA"
    CBE = "CBE"
    CHICAGO = "CHI"

    FORMAT_CHOICES = (
            (MLA, "MLA"),
            (APA, "APA"),
            (CBE, "CBE"),
            (CHICAGO, "Chicago"),
    )
    format = models.CharField(max_length= 10,
                              choices=FORMAT_CHOICES)

    def isRightExt(paper):
        extension = paper.rsplit('.')[1]
        print(extension)
        return extension == 'pdf' or extension == 'doc' or extension == 'docx'

    def pcm_is_not_author(pcm, self):
        return pcm != self.contact_author

    def __str__(self):
        return self.title

class NotificationTemplate(models.Model):
    text = models.CharField(max_length = 250)
    key = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)
    type = models.PositiveSmallIntegerField()

    def __str__(self):
        return 'Template'+str(self.type)

class Notification(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    text = models.CharField(max_length = 50)

class UserNotification(models.Model):
    user = models.ForeignKey(SAM2017User)
    notification = models.ForeignKey(Notification)
    viewed = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    last_touched = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.user.username

class Deadline(models.Model):
    date = models.DateTimeField()
    notification = models.ForeignKey(UserNotification)

    def __str__(self):
        return self.notification.user.user.username+' Deadline'

class PCMAssign(models.Model):
    paper = models.ForeignKey(Paper)
    pcm = models.ForeignKey(SAM2017User)

    def __str__(self):
        return self.paper.title+'_'+self.pcm.user.username

class PCMPickList(models.Model):
    pcm = models.ForeignKey(SAM2017User)
    paper = models.ForeignKey(Paper)

    def __str__(self):
        return self.paper.title+'_'+self.pcm.user.username

class PCMReview(models.Model):
    pcm = models.ForeignKey(SAM2017User)
    paper = models.ForeignKey(Paper)
    grade = models.PositiveSmallIntegerField(validators=[MaxValueValidator(100)])
    comment = models.TextField(max_length = 256)

    def __str__(self):
        return self.pcm.user.username+'_'+self.paper.title+'_review'

    def is_last_review(paper1):
        reviews = PCMReview.objects.filter(paper=paper1)
        return len(reviews) >= 3

class PCCReview(models.Model):
    paper = models.ForeignKey(Paper)
    pcc = models.ForeignKey(SAM2017User)
    final_grade = models.CharField(max_length= 2)
    comment = models.TextField(max_length = 256)

    def __str__(self):
        return self.paper.title+'Final Review'

