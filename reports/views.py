import csv
import datetime
from django.http import HttpResponse
from django.shortcuts import render

from accounts.mixins import RoleRequiredMixin, MANAGEMENT_ROLES, FINANCE_ROLES
from django.views import View

from students.models import Student
from attendance.models import StudentAttendance
from fees.models import FeePayment, Income, Expense

REPORT_TYPES = {
    "students": {"label": "Students", "date_field": "admission_date", "allowed_roles": MANAGEMENT_ROLES + ["TEACHER"]},
    "attendance": {"label": "Attendance", "date_field": "date", "allowed_roles": MANAGEMENT_ROLES + ["TEACHER"]},
    "fees": {"label": "Fee Payments", "date_field": "due_date", "allowed_roles": FINANCE_ROLES},
    "income": {"label": "Income & Funding", "date_field": "date", "allowed_roles": FINANCE_ROLES},
    "expenses": {"label": "Expenses", "date_field": "date", "allowed_roles": FINANCE_ROLES},
    "exams": {"label": "Exam Results", "date_field": "exam__start_date", "allowed_roles": MANAGEMENT_ROLES},
    "hifz": {"label": "Quran Progress", "date_field": "date", "allowed_roles": MANAGEMENT_ROLES + ["TEACHER"]},
    "inventory": {"label": "Inventory Stock", "date_field": None, "allowed_roles": MANAGEMENT_ROLES + ["STAFF"]},
    "library": {"label": "Library Issues", "date_field": "issued_on", "allowed_roles": MANAGEMENT_ROLES + ["LIBRARIAN"]},
}


def _get_queryset(report_type, start_date, end_date):
    if report_type == "students":
        qs = Student.objects.select_related("section", "section__school_class").all()
        if start_date:
            qs = qs.filter(admission_date__gte=start_date)
        if end_date:
            qs = qs.filter(admission_date__lte=end_date)
        rows = [["Admission #", "Name", "Section", "Gender", "Status", "Admission Date", "Guardian", "Guardian Phone"]]
        for s in qs:
            rows.append([s.admission_number, s.full_name, str(s.section or "-"), s.get_gender_display(),
                         s.get_status_display(), str(s.admission_date), s.guardian_name, s.guardian_phone])
        return rows

    if report_type == "attendance":
        qs = StudentAttendance.objects.select_related("student").all()
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        rows = [["Date", "Student", "Admission #", "Status", "Remarks"]]
        for a in qs.order_by("-date"):
            rows.append([str(a.date), a.student.full_name, a.student.admission_number, a.get_status_display(), a.remarks])
        return rows

    if report_type == "fees":
        qs = FeePayment.objects.select_related("student", "fee_structure").all()
        if start_date:
            qs = qs.filter(due_date__gte=start_date)
        if end_date:
            qs = qs.filter(due_date__lte=end_date)
        rows = [["Receipt #", "Student", "Fee", "Amount Due", "Amount Paid", "Balance", "Status", "Due Date", "Paid On"]]
        for p in qs.order_by("-due_date"):
            rows.append([p.receipt_number or "-", p.student.full_name, p.fee_structure.name, str(p.amount_due),
                         str(p.amount_paid), str(p.balance()), p.get_status_display(), str(p.due_date), str(p.paid_on or "-")])
        return rows

    if report_type == "income":
        qs = Income.objects.all()
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        rows = [["Date", "Donor / Source", "Type", "Amount", "Contact", "Notes"]]
        for i in qs.order_by("-date"):
            rows.append([str(i.date), i.donor_name, i.get_income_type_display(), str(i.amount), i.contact_number, i.notes])
        return rows

    if report_type == "expenses":
        qs = Expense.objects.all()
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        rows = [["Date", "Title", "Category", "Amount", "Notes"]]
        for e in qs.order_by("-date"):
            rows.append([str(e.date), e.title, e.category, str(e.amount), e.notes])
        return rows

    if report_type == "exams":
        from exams.models import ExamResult
        qs = ExamResult.objects.select_related("exam", "student", "subject")
        if start_date:
            qs = qs.filter(exam__start_date__gte=start_date)
        if end_date:
            qs = qs.filter(exam__start_date__lte=end_date)
        rows = [["Exam", "Class", "Student", "Admission #", "Subject", "Obtained", "Total", "%", "Grade"]]
        for r in qs.order_by("exam__start_date", "student__admission_number", "subject__name"):
            rows.append([r.exam.name, r.exam.school_class.name, r.student.full_name, r.student.admission_number,
                         r.subject.name, str(r.obtained_marks), str(r.total_marks), str(r.percentage), r.grade])
        return rows

    if report_type == "hifz":
        from hifz.models import HifzRecord
        qs = HifzRecord.objects.select_related("student")
        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        rows = [["Date", "Student", "Admission #", "Type", "Para", "Portion", "Performance", "Remarks"]]
        for h in qs:
            rows.append([str(h.date), h.student.full_name, h.student.admission_number, h.get_kind_display(),
                         str(h.para), h.portion, h.get_performance_display(), h.remarks])
        return rows

    if report_type == "inventory":
        from inventory.models import Item
        rows = [["Item", "Category", "Quantity", "Unit", "Min. Level", "Location", "Low Stock"]]
        for i in Item.objects.all():
            rows.append([i.name, i.get_category_display(), str(i.quantity), i.unit, str(i.min_quantity), i.location, "Yes" if i.is_low else "No"])
        return rows

    if report_type == "library":
        from library.models import BookIssue
        qs = BookIssue.objects.select_related("book", "student", "teacher__user")
        if start_date:
            qs = qs.filter(issued_on__gte=start_date)
        if end_date:
            qs = qs.filter(issued_on__lte=end_date)
        rows = [["Book", "Borrower", "Issued", "Due", "Returned", "Fine (Rs)"]]
        for i in qs:
            rows.append([i.book.title, str(i.borrower), str(i.issued_on), str(i.due_date), str(i.returned_on or "-"), str(i.fine)])
        return rows

    return [["No data"]]


class ReportsIndexView(RoleRequiredMixin, View):
    template_name = "reports/index.html"
    allowed_roles = MANAGEMENT_ROLES + ["TEACHER", "ACCOUNTANT"]

    def get(self, request):
        # Only offer report types the current user's role is allowed to export
        user = request.user
        available = {}
        for key, meta in REPORT_TYPES.items():
            if user.is_superuser or user.role in meta["allowed_roles"]:
                available[key] = meta["label"]
        return render(request, self.template_name, {"report_types": available})


class ReportsExportView(RoleRequiredMixin, View):
    allowed_roles = MANAGEMENT_ROLES + ["TEACHER", "ACCOUNTANT"]

    def get(self, request):
        report_type = request.GET.get("type")
        fmt = request.GET.get("format", "csv")
        start_date = request.GET.get("start_date") or None
        end_date = request.GET.get("end_date") or None

        meta = REPORT_TYPES.get(report_type)
        if not meta:
            return HttpResponse("Invalid report type.", status=400)
        if not (request.user.is_superuser or request.user.role in meta["allowed_roles"]):
            return HttpResponse("You do not have permission to export this report.", status=403)

        rows = _get_queryset(report_type, start_date, end_date)
        filename_bits = [report_type]
        if start_date:
            filename_bits.append(f"from-{start_date}")
        if end_date:
            filename_bits.append(f"to-{end_date}")
        filename = "_".join(filename_bits) or report_type

        if fmt == "pdf":
            return self._export_pdf(rows, filename, meta["label"], start_date, end_date)
        return self._export_csv(rows, filename)

    def _export_csv(self, rows, filename):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        writer = csv.writer(response)
        for row in rows:
            writer.writerow(row)
        return response

    def _export_pdf(self, rows, filename, label, start_date, end_date):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        styles = getSampleStyleSheet()
        elements = []

        title = f"Jamia Rahmania Rizvia Sohawa — {label} Report"
        subtitle_bits = []
        if start_date:
            subtitle_bits.append(f"From: {start_date}")
        if end_date:
            subtitle_bits.append(f"To: {end_date}")
        subtitle_bits.append(f"Generated: {datetime.date.today()}")

        elements.append(Paragraph(title, styles["Title"]))
        elements.append(Paragraph(" | ".join(subtitle_bits), styles["Normal"]))
        elements.append(Spacer(1, 0.5 * cm))

        table = Table(rows, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b1e3d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
        return response
