from django import forms
from django.contrib.auth.models import User

class PCCReviewForm(forms.Form):
    GRADE_CHOICES = (
            ('A', "A"),
            ('A-', "A-"),
            ('B+', "B+"),
            ('B', "B"),
            ('B-', "B-"),
            ('C+', "C+"),
            ('C', "C"),
            ('C-', "C-"),
            ('D+', "D+"),
            ('D', "D"),
            ('D-', "D-"),
            ('F', "F")
    )

    grade = forms.ChoiceField(label='overall grade of paper', choices = GRADE_CHOICES, required=True)
    comment = forms.CharField(widget=forms.Textarea, label='review comment', max_length=256, required=True)

class PCMReviewForm(forms.Form):
    grade = forms.IntegerField(label='grade of paper', required=True, max_value=100, min_value=0)
    comment = forms.CharField(widget=forms.Textarea, label='review comment', max_length=256, required=True)

class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label='Select a file',
        help_text='max. 42 megabytes',
        widget=forms.FileInput(attrs={'class' : 'input-file uniform_on'}),
    )

    FORMAT_CHOICES = (
            ('MLA', "MLA"),
            ('APA', "APA"),
            ('CBE', "CBE"),
            ('CHICAGO', "Chicago"),
    )
    title = forms.CharField(label='Title', max_length=225, widget=forms.TextInput(attrs={'class' : 'span6 typeahead'}))
   # revision = forms.CharField(label='revision', max_length=2, widget=forms.TextInput(attrs={'class' : 'span6 typeahead'}))
    authors = forms.CharField(label='list of authors', max_length=200, widget=forms.TextInput(attrs={'class' : 'span6 typeahead'}))
    format = forms.ChoiceField(label='format of paper', widget=forms.Select, choices = FORMAT_CHOICES, required= True)
    help_text='max. 42 megabytes'

class ReuploadForm(forms.Form):
    docfile = forms.FileField(
        label='Select a file',
        help_text='max. 42 megabytes',
        widget=forms.FileInput(attrs={'class' : 'input-file uniform_on'}),
    )
    help_text='max. 42 megabytes'

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ( 'first_name', 'last_name', 'username', 'email', 'password' )

class RegisterUser(forms.ModelForm):

    password_confirm = forms.CharField()

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']


    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if not password_confirm:
            raise forms.ValidationError("You must confirm your password")
        if password != password_confirm:
            raise forms.ValidationError("Your passwords did not match")
        return password_confirm

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not email:
            raise forms.ValidationError("You must enter an email")

        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')

        if not first_name:
            raise forms.ValidationError("You must enter your first name")

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')

        if not last_name:
            raise forms.ValidationError("You must enter your last name")

        return last_name

class ChangePasswordForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_new_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = [ 'password' ]


    def clean_confirm_new_password(self):
        password = self.cleaned_data.get('password')
        confirm_new_password = self.cleaned_data.get('confirm_new_password')

        if not confirm_new_password:
            raise forms.ValidationError("You must confirm your password")
        if password != confirm_new_password:
            raise forms.ValidationError("Your passwords did not match")
        return confirm_new_password

class UpdateProfileForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'id' : 'fname',}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'id' : 'lname',}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'id' : 'email'}))

    class Meta:
        model = User
        fields = [ 'first_name', 'last_name', 'email' ]


    def clean_email(self):
        email = self.cleaned_data.get('email')

        if not email:
            raise forms.ValidationError("You must enter an email")

        return email

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')

        if not first_name:
            raise forms.ValidationError("You must enter your first name")

        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')

        if not last_name:
            raise forms.ValidationError("You must enter your last name")

        return last_name


