import datetime
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.db.models import Q

from accounts.decorators import role_required
from accounts.mixins import RoleRequiredMixin, MANAGEMENT_ROLES, STAFF_ROLES
from .forms import BookForm, IssueForm
from .models import Book, BookIssue

LIBRARY_ROLES = MANAGEMENT_ROLES + ["LIBRARIAN"]


class BookListView(RoleRequiredMixin, ListView):
    model = Book
    template_name = "library/book_list.html"
    context_object_name = "books"
    paginate_by = 20
    allowed_roles = STAFF_ROLES

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(author__icontains=q) | Q(category__icontains=q) | Q(isbn__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["can_edit"] = self.request.user.is_superuser or self.request.user.role in LIBRARY_ROLES
        return ctx


class BookCreateView(RoleRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "partials/form.html"
    success_url = reverse_lazy("library:books")
    extra_context = {"title": "Add Book"}
    allowed_roles = LIBRARY_ROLES


class BookUpdateView(RoleRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "partials/form.html"
    success_url = reverse_lazy("library:books")
    extra_context = {"title": "Edit Book"}
    allowed_roles = LIBRARY_ROLES


class BookDeleteView(RoleRequiredMixin, DeleteView):
    model = Book
    template_name = "partials/confirm_delete.html"
    success_url = reverse_lazy("library:books")
    allowed_roles = LIBRARY_ROLES


class IssueListView(RoleRequiredMixin, ListView):
    model = BookIssue
    template_name = "library/issue_list.html"
    context_object_name = "issues"
    paginate_by = 25
    allowed_roles = LIBRARY_ROLES

    def get_queryset(self):
        qs = BookIssue.objects.select_related("book", "student", "teacher__user")
        if self.request.GET.get("status") == "out":
            qs = qs.filter(returned_on__isnull=True)
        return qs


class IssueCreateView(RoleRequiredMixin, CreateView):
    model = BookIssue
    form_class = IssueForm
    template_name = "partials/form.html"
    success_url = reverse_lazy("library:issues")
    extra_context = {"title": "Issue Book"}
    allowed_roles = LIBRARY_ROLES

    def get_initial(self):
        return {"issued_on": datetime.date.today(), "due_date": datetime.date.today() + datetime.timedelta(days=14)}


@role_required(*LIBRARY_ROLES)
def return_book(request, pk):
    issue = get_object_or_404(BookIssue, pk=pk)
    if request.method == "POST" and not issue.returned_on:
        issue.returned_on = datetime.date.today()
        issue.save()
        msg = "Book returned."
        if issue.fine:
            msg += f" Overdue fine: Rs {issue.fine}."
        messages.success(request, msg)
    return redirect("library:issues")
