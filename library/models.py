import datetime
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models

FINE_PER_DAY = Decimal("5")  # Rs per overdue day


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=100, blank=True, help_text="e.g. Tafseer, Hadith, Fiqh, Seerah, Urdu, English")
    language = models.CharField(max_length=50, blank=True, help_text="e.g. Arabic, Urdu, English")
    isbn = models.CharField("ISBN / Book No.", max_length=30, blank=True)
    copies = models.PositiveIntegerField(default=1)
    shelf = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def issued_count(self):
        return self.issues.filter(returned_on__isnull=True).count()

    @property
    def available(self):
        return max(self.copies - self.issued_count, 0)


class BookIssue(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="issues")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, null=True, blank=True, related_name="book_issues")
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, null=True, blank=True, related_name="book_issues")
    issued_on = models.DateField(default=datetime.date.today)
    due_date = models.DateField()
    returned_on = models.DateField(null=True, blank=True)
    fine_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ["-issued_on", "-id"]

    def clean(self):
        if bool(self.student_id) == bool(self.teacher_id):
            raise ValidationError("Choose either a student or a teacher as the borrower (not both).")
        if self.due_date and self.issued_on and self.due_date < self.issued_on:
            raise ValidationError("Due date cannot be before the issue date.")
        if not self.pk and self.book_id and self.book.available < 1:
            raise ValidationError("No copies of this book are currently available.")

    @property
    def borrower(self):
        return self.student or self.teacher

    @property
    def is_returned(self):
        return self.returned_on is not None

    @property
    def overdue_days(self):
        end = self.returned_on or datetime.date.today()
        return max((end - self.due_date).days, 0)

    @property
    def fine(self):
        return FINE_PER_DAY * self.overdue_days

    def __str__(self):
        return f"{self.book} → {self.borrower}"
