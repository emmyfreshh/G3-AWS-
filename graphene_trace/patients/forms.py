from django import forms
from .models import Comment, PressureData

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text', 'pressure_data']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pressure_data'].queryset = user.pressure_data.all()

class PressureDataForm(forms.ModelForm):
    class Meta:
        model = PressureData
        fields = ['pressure_value', 'sensor_location']
        widgets = {
            'pressure_value': forms.NumberInput(attrs={'step': '0.1'}),
        }