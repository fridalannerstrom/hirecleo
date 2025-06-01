

class TestChatMessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, required=True)
