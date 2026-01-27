from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'email', 'phone', 'address', 'notes']   # ← add 'email' here
        
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your@email.com'}),  # ← add this
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '024 XXX XXXX'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Delivery Address'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any special instructions (optional)'}),
        }