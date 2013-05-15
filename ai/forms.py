from django import forms
# Create your models here.


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField(
        label='Select a file'
    )
