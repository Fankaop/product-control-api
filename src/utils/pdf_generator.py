from fpdf import FPDF

from data.models.batch import Batch
from data.models.product import Product


class _BatchPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Batch Report", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str) -> None:
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(45, 106, 159)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, title, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def key_value(self, key: str, value: str) -> None:
        self.set_font("Helvetica", "B", 10)
        self.cell(60, 7, key + ":", new_x="RIGHT", new_y="LAST")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")

    def table_header(self, cols: list[tuple[str, int]]) -> None:
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(45, 106, 159)
        self.set_text_color(255, 255, 255)
        for label, width in cols:
            self.cell(width, 7, label, border=1, fill=True, align="C")
        self.ln()
        self.set_text_color(0, 0, 0)

    def table_row(self, values: list[tuple[str, int]], fill: bool = False) -> None:
        self.set_font("Helvetica", "", 9)
        if fill:
            self.set_fill_color(235, 240, 248)
        for text, width in values:
            self.cell(width, 6, str(text)[:40], border=1, fill=fill)
        self.ln()


def generate_batch_pdf(batch: Batch, products: list[Product]) -> str:
    pdf = _BatchPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # --- Section 1: Batch info ---
    pdf.section_title("Batch Information")
    pdf.key_value("Batch Number", str(batch.batch_number))
    pdf.key_value("Batch Date", str(batch.batch_date))
    pdf.key_value("Status", "Closed" if batch.is_closed else "Open")
    pdf.key_value("Task Description", batch.task_description)
    pdf.key_value("Nomenclature", batch.nomenclature)
    pdf.key_value("EKN Code", batch.ekn_code)
    pdf.key_value("Shift", batch.shift)
    pdf.key_value("Team", batch.team)
    pdf.key_value("Shift Start", str(batch.shift_start))
    pdf.key_value("Shift End", str(batch.shift_end))
    pdf.ln(4)

    # --- Section 2: Statistics ---
    total = len(products)
    aggregated = sum(1 for p in products if p.is_aggregated)
    remaining = total - aggregated
    rate = round(aggregated / total * 100, 1) if total > 0 else 0.0

    pdf.section_title("Statistics")
    pdf.key_value("Total Products", str(total))
    pdf.key_value("Aggregated", str(aggregated))
    pdf.key_value("Remaining", str(remaining))
    pdf.key_value("Completion Rate", f"{rate}%")
    pdf.ln(4)

    # --- Section 3: Product list ---
    pdf.section_title("Products")
    cols = [("ID", 20), ("Unique Code", 70), ("Aggregated", 30), ("Aggregated At", 60)]
    pdf.table_header(cols)

    for i, product in enumerate(products):
        agg_at = str(product.aggregated_at) if product.aggregated_at else "-"
        pdf.table_row([
            (str(product.id), 20),
            (product.unique_code, 70),
            ("Yes" if product.is_aggregated else "No", 30),
            (agg_at, 60),
        ], fill=i % 2 == 0)

    path = f"/tmp/batch_{batch.id}_report.pdf"
    pdf.output(path)
    return path
