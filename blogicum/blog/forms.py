from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'category', 'location', 'image', 'pub_date']
        widgets = {'pub_date': forms.DateTimeInput(attrs={'type': 'date'})}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
