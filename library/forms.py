from django import forms
from accounts.widgets import BootstrapModelForm
from .models import Book, BookIssue


class BookForm(BootstrapModelForm):
    class Meta:
        model = Book
        fields = ["title", "author", "category", "language", "isbn", "copies", "shelf"]


class IssueForm(BootstrapModelForm):
    class Meta:
        model = BookIssue
        fields = ["book", "student", "teacher", "issued_on", "due_date"]
