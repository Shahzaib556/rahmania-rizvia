from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.BookListView.as_view(), name="books"),
    path("add/", views.BookCreateView.as_view(), name="book_add"),
    path("<int:pk>/edit/", views.BookUpdateView.as_view(), name="book_edit"),
    path("<int:pk>/delete/", views.BookDeleteView.as_view(), name="book_delete"),
    path("issues/", views.IssueListView.as_view(), name="issues"),
    path("issues/add/", views.IssueCreateView.as_view(), name="issue_add"),
    path("issues/<int:pk>/return/", views.return_book, name="return"),
]
