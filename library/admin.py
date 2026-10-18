from django.contrib import admin
from .models import Book, BookIssue


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "copies")
    search_fields = ("title", "author", "isbn")


admin.site.register(BookIssue)
