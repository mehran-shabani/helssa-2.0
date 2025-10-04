"""
Forms for the chatbot app.
"""
from django import forms


class ChatMessageForm(forms.Form):
    """Form for validating chat message input."""

    message = forms.CharField(
        max_length=4000,
        required=True,
        widget=forms.Textarea(attrs={"placeholder": "Ask a medical question..."}),
    )
    model = forms.ChoiceField(
        choices=[
            ("gpt-4o-mini", "GPT-4O Mini (Fast)"),
            ("gpt-4o", "GPT-4O (Advanced)"),
            ("o1", "O1 (Reasoning)"),
        ],
        required=False,
        initial="gpt-4o-mini",
    )
    files = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
    )
