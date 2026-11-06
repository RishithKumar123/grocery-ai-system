import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.core.database import get_db
from app.core.config import settings
from app.data.models.store_model import StoreModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.product_model import ProductModel
from app.data.models.order_model import OrderModel
from app.data.models.user_model import UserModel
from app.data.models.report_model import ReportModel
from app.data.models.supplier_model import SupplierModel
from app.data.models.brand_model import BrandModel
from app.data.models.category_model import CategoryModel
from app.data.models.stock_transaction_model import StockTransactionModel
from app.data.models.ai_scan_model import AIScanModel, AIScanDetectionModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from pydantic import BaseModel

# openpyxl excel generators
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# reportlab pdf generators
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

router = APIRouter(prefix="/reports", tags=["reports"])


class OperationalReportRequest(BaseModel):
    store_id: int
    report_type: str  # "stock" | "purchase" | "sales" | "supplier" | "category" | "brand" | "valuation"
    format: str  # "excel" | "pdf"


def get_operational_data(db: Session, store_id: int, report_type: str):
    """Retrieve filtered records and aggregate summaries for operational reporting."""
    store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
    if not store:
        raise ValueError("Store branch not found.")

    if report_type == "stock":
        items = db.query(InventoryModel).filter(InventoryModel.store_id == store_id).all()
        return {
            "title": f"Stock Level Report - {store.name}",
            "headers": ["Product Name", "SKU", "Qty", "Available", "Reserved", "Damaged", "Location", "Min Stock", "Status"],
            "rows": [
                [
                    item.name,
                    item.sku,
                    item.quantity,
                    item.available_stock,
                    item.reserved_stock,
                    item.damaged_stock,
                    item.location_bin,
                    item.min_stock,
                    item.status
                ]
                for item in items
            ]
        }

    elif report_type == "purchase":
        txs = db.query(StockTransactionModel).filter(
            and_(StockTransactionModel.store_id == store_id, StockTransactionModel.transaction_type == "Purchase")
        ).order_by(StockTransactionModel.created_at.desc()).all()
        return {
            "title": f"Purchase Replenishment Ledger - {store.name}",
            "headers": ["Date", "Product Name", "SKU", "Added Qty", "Previous Qty", "New Qty", "Operator Note"],
            "rows": [
                [
                    tx.created_at.strftime("%Y-%m-%d %H:%M"),
                    tx.product.name if tx.product else "N/A",
                    tx.product.sku if tx.product else "N/A",
                    f"+{tx.quantity_change}",
                    tx.previous_quantity,
                    tx.new_quantity,
                    tx.notes or "-"
                ]
                for tx in txs
            ]
        }

    elif report_type == "sales":
        txs = db.query(StockTransactionModel).filter(
            and_(StockTransactionModel.store_id == store_id, StockTransactionModel.transaction_type == "Sale")
        ).order_by(StockTransactionModel.created_at.desc()).all()
        return {
            "title": f"Sales Outflow Ledger - {store.name}",
            "headers": ["Date", "Product Name", "SKU", "Sold Qty", "Price", "Est Revenue", "Operator Note"],
            "rows": [
                [
                    tx.created_at.strftime("%Y-%m-%d %H:%M"),
                    tx.product.name if tx.product else "N/A",
                    tx.product.sku if tx.product else "N/A",
                    f"{tx.quantity_change}",
                    f"₹{float(tx.product.price if tx.product else 0):.2f}",
                    f"₹{float(abs(tx.quantity_change) * (tx.product.price if tx.product else 0)):.2f}",
                    tx.notes or "-"
                ]
                for tx in txs
            ]
        }

    elif report_type == "supplier":
        suppliers = db.query(SupplierModel).all()
        return {
            "title": f"Supplier Registry - {store.name}",
            "headers": ["Supplier Name", "Contact Person", "Email", "Phone", "Payment Terms", "Configured Tax Region", "Status"],
            "rows": [
                [
                    s.name,
                    s.contact_person or "-",
                    s.email or "-",
                    s.phone or "-",
                    s.payment_terms or "-",
                    s.gst_vat_number or "-",
                    "Active" if s.is_active else "Inactive"
                ]
                for s in suppliers
            ]
        }

    elif report_type == "category":
        # Group inventory quantity and valuation by product category
        items = db.query(InventoryModel).filter(InventoryModel.store_id == store_id).all()
        categories = {}
        for item in items:
            prod = item.product
            cat = prod.category if prod else "General/Unmapped"
            price = float(prod.price if prod else 0.0)
            val = float(item.quantity) * price
            if cat not in categories:
                categories[cat] = {"skus": 0, "quantity": 0, "value": 0.0}
            categories[cat]["skus"] += 1
            categories[cat]["quantity"] += item.quantity
            categories[cat]["value"] += val

        return {
            "title": f"Inventory Metrics By Category - {store.name}",
            "headers": ["Category Name", "Catalog SKUs Count", "Total Stock Units", "Current Market Valuation"],
            "rows": [
                [
                    cat,
                    stats["skus"],
                    stats["quantity"],
                    f"₹{stats['value']:.2f}"
                ]
                for cat, stats in categories.items()
            ]
        }

    elif report_type == "brand":
        # Group inventory quantity and valuation by product brand
        items = db.query(InventoryModel).filter(InventoryModel.store_id == store_id).all()
        brands = {}
        for item in items:
            prod = item.product
            brand_name = prod.brand if (prod and prod.brand) else "No Brand"
            price = float(prod.price if prod else 0.0)
            val = float(item.quantity) * price
            if brand_name not in brands:
                brands[brand_name] = {"skus": 0, "quantity": 0, "value": 0.0}
            brands[brand_name]["skus"] += 1
            brands[brand_name]["quantity"] += item.quantity
            brands[brand_name]["value"] += val

        return {
            "title": f"Inventory Metrics By Brand - {store.name}",
            "headers": ["Brand Name", "Catalog SKUs Count", "Total Stock Units", "Current Market Valuation"],
            "rows": [
                [
                    brand,
                    stats["skus"],
                    stats["quantity"],
                    f"₹{stats['value']:.2f}"
                ]
                for brand, stats in brands.items()
            ]
        }

    elif report_type == "valuation":
        items = db.query(InventoryModel).filter(InventoryModel.store_id == store_id).all()
        return {
            "title": f"Inventory Valuation Sheet - {store.name}",
            "headers": ["Product Name", "SKU", "Price", "Cost Price", "Quantity", "Selling Valuation", "Cost Valuation", "Estimated Margin"],
            "rows": [
                [
                    item.name,
                    item.sku,
                    f"₹{float(item.product.price if item.product else 0):.2f}",
                    f"₹{float(item.product.cost_price if item.product else 0):.2f}",
                    item.quantity,
                    f"₹{float(item.quantity * (item.product.price if item.product else 0)):.2f}",
                    f"₹{float(item.quantity * (item.product.cost_price if item.product else 0)):.2f}",
                    f"₹{float(item.quantity * ((item.product.price if item.product else 0) - (item.product.cost_price if item.product else 0))):.2f}"
                ]
                for item in items
            ]
        }

    else:
        raise ValueError("Invalid operational report type.")


def generate_excel_report(data: dict, file_path: str):
    """Generate operational Excel spreadsheet workbook."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Report Ledger"
    ws.views.sheetView[0].showGridLines = True

    emerald_fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
    dark_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    white_font_bold = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    bold_font = Font(name="Segoe UI", size=10, bold=True)
    normal_font = Font(name="Segoe UI", size=10)
    title_font = Font(name="Segoe UI", size=12, bold=True, color="FFFFFF")
    meta_font = Font(name="Segoe UI", size=9, italic=True, color="64748B")

    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )

    header_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    # Banner Title
    ws.merge_cells("A1:I2")
    banner = ws["A1"]
    banner.value = f"  AETHERIA RETAL GROUP - {data['title'].upper()}"
    banner.font = title_font
    banner.fill = dark_fill
    banner.alignment = Alignment(horizontal="left", vertical="center")

    ws["A3"] = f"Operational Intelligence Ledger | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ws["A3"].font = meta_font

    # Headers Row at row 5
    ws.row_dimensions[5].height = 24
    for col_idx, header in enumerate(data["headers"], 1):
        cell = ws.cell(row=5, column=col_idx)
        cell.value = header
        cell.font = white_font_bold
        cell.fill = emerald_fill
        cell.alignment = header_align
        cell.border = thin_border

    row_idx = 6
    for row_val in data["rows"]:
        ws.row_dimensions[row_idx].height = 20
        for col_idx, val in enumerate(row_val, 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = normal_font
            cell.border = thin_border
            cell.alignment = left_align
            if row_idx % 2 == 0:
                cell.fill = zebra_fill
        row_idx += 1

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.row in [1, 2]:
                continue
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    wb.save(file_path)


def generate_pdf_report(data: dict, file_path: str):
    """Generate operational PDF document."""
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    th_style = ParagraphStyle(
        'TableHead',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.white,
        alignment=1 # Center
    )
    tb_style = ParagraphStyle(
        'TableBody',
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#1E293B')
    )

    story = []

    # Title
    story.append(Paragraph(data["title"], title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Aetheria Systems Operational Intelligence Feed", meta_style))
    story.append(Spacer(1, 10))

    # Prep Table
    table_data = []
    
    # Header row
    header_row = [Paragraph(h, th_style) for h in data["headers"]]
    table_data.append(header_row)

    # Body rows
    for row in data["rows"]:
        body_row = [Paragraph(str(val), tb_style) for val in row]
        table_data.append(body_row)

    # Calculate column widths to span 540 pt printable width (612 - 72)
    col_count = len(data["headers"])
    col_width = 540.0 / col_count

    table = Table(table_data, colWidths=[col_width] * col_count)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))

    story.append(table)
    doc.build(story)


@router.post("/operational", status_code=status.HTTP_201_CREATED)
def generate_operational_report(
    payload: OperationalReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API endpoint to compile and export specific store reports (PDF / Excel)."""
    try:
        report_data = get_operational_data(
            db=db,
            store_id=payload.store_id,
            report_type=payload.report_type
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))

    # Prep output paths
    reports_dir = os.path.join(settings.LOCAL_STORAGE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    fmt = payload.format.lower().strip()
    ext = "xlsx" if fmt == "excel" else "pdf"
    file_name = f"op_report_{payload.report_type}_{payload.store_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    file_path = os.path.join(reports_dir, file_name)
    file_url = f"/static/uploads/reports/{file_name}"

    try:
        if fmt == "excel":
            generate_excel_report(report_data, file_path)
        else:
            generate_pdf_report(report_data, file_path)
    except Exception as run_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report format structure: {str(run_err)}"
        )

    # Save to reports catalog db table
    report_record = ReportModel(
        store_id=payload.store_id,
        generated_by_id=current_user.id,
        type=fmt.upper(),
        file_url=file_url,
        parameters={"generated_at": datetime.now().isoformat(), "report_type": payload.report_type}
    )
    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    return {"file_url": file_url}


def generate_store_excel_report_internal(
    db: Session,
    store_id: int,
    user_id: int,
    scan_id: int = None
) -> str:
    """
    Internal helper to generate a highly formatted multi-sheet Excel report.
    Can be invoked dynamically from API routes or background process worker tasks.
    """
    store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
    if not store:
        raise ValueError("Store branch not found.")

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    user_name = user.full_name if user else "System Administrator"

    # Fetch inventory items
    inventory_items = db.query(InventoryModel).filter(
        InventoryModel.store_id == store_id
    ).all()

    wb = Workbook()
    
    # Theme configuration (Emerald and Slate)
    emerald_fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
    dark_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    zebra_fill = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")
    alert_fill = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")
    yellow_fill = PatternFill(start_color="FEFCE8", end_color="FEFCE8", fill_type="solid")

    white_font_bold = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    bold_font = Font(name="Segoe UI", size=11, bold=True)
    normal_font = Font(name="Segoe UI", size=10)
    title_font = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
    meta_font = Font(name="Segoe UI", size=9, italic=True, color="64748B")

    thin_border = Border(
        left=Side(style='thin', color='E2E8F0'),
        right=Side(style='thin', color='E2E8F0'),
        top=Side(style='thin', color='E2E8F0'),
        bottom=Side(style='thin', color='E2E8F0')
    )
    
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center")
    center_align = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")

    # --- SHEET 1: INVENTORY CATALOG ---
    ws_inv = wb.active
    ws_inv.title = "Inventory"
    ws_inv.views.sheetView[0].showGridLines = True

    # Logo / Title Banner (A1:G2)
    ws_inv.merge_cells("A1:G2")
    banner = ws_inv["A1"]
    banner.value = f"  AETHERIA RETAIL GROUP - {store.name.upper()}"
    banner.font = title_font
    banner.fill = dark_fill
    banner.alignment = Alignment(horizontal="left", vertical="center")

    # Time and Date details
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    ws_inv["A3"] = f"Inventory Status Report | Generated: {now_str}"
    ws_inv["A3"].font = meta_font
    
    ws_inv["A4"] = f"Operator: {user_name} | Assigned Branch: {store.name}"
    ws_inv["A4"].font = Font(name="Segoe UI", size=10, bold=True, color="1E293B")

    start_row = 6
    if scan_id:
        scan = db.query(AIScanModel).filter(AIScanModel.id == scan_id).first()
        if scan:
            ws_inv["A5"] = "--- AI SCAN PERFORMANCE STATISTICS ---"
            ws_inv["A5"].font = Font(name="Segoe UI", size=10, bold=True, color="059669")
            
            s_time = scan.scan_start_time.strftime("%I:%M:%S %p") if scan.scan_start_time else "N/A"
            e_time = scan.scan_end_time.strftime("%I:%M:%S %p") if scan.scan_end_time else "N/A"
            dur = f"{scan.scan_duration:.2f} Seconds" if scan.scan_duration else "N/A"
            fps_val = f"{scan.fps:.2f} FPS" if scan.fps else "N/A"

            ws_inv["A6"] = f"Scan ID: #SCN-{scan.id} | Date: {scan.created_at.strftime('%Y-%m-%d')}"
            ws_inv["A6"].font = normal_font
            ws_inv["A7"] = f"Start Time: {s_time} | End Time: {e_time}"
            ws_inv["A7"].font = normal_font
            ws_inv["A8"] = f"Total Scan Time: {dur} | Performance Speed: {fps_val}"
            ws_inv["A8"].font = Font(name="Segoe UI", size=10, bold=True, color="1E293B")
            start_row = 10

    # Headers Row at start_row
    ws_inv.row_dimensions[start_row].height = 26
    headers = ["Item ID", "Product Name", "SKU", "Shelf Location", "Stock Quantity", "Confidence", "Status"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws_inv.cell(row=start_row, column=col_idx)
        cell.value = header
        cell.font = white_font_bold
        cell.fill = emerald_fill
        cell.alignment = header_align
        cell.border = thin_border

    row_idx = start_row + 1
    for item in inventory_items:
        ws_inv.row_dimensions[row_idx].height = 20
        row_values = [
            item.id,
            item.name,
            item.sku,
            item.location_bin or "Main Aisle",
            item.quantity,
            f"{int(item.confidence * 100)}%" if item.confidence else "N/A",
            item.status
        ]
        for col_idx, val in enumerate(row_values, 1):
            cell = ws_inv.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.font = normal_font
            cell.border = thin_border
            
            if col_idx in [1, 5, 6]:
                cell.alignment = center_align
            else:
                cell.alignment = left_align

            if row_idx % 2 == 0:
                cell.fill = zebra_fill
        row_idx += 1

    totals_row = row_idx
    ws_inv.row_dimensions[totals_row].height = 22
    ws_inv.cell(row=totals_row, column=4, value="Total Stock Quantity:").font = bold_font
    ws_inv.cell(row=totals_row, column=4).alignment = right_align
    
    qty_cell = ws_inv.cell(row=totals_row, column=5)
    qty_cell.value = f"=SUM(E{start_row+1}:E{totals_row-1})"
    qty_cell.font = bold_font
    qty_cell.alignment = center_align
    qty_cell.border = Border(top=Side(style='thin', color='000000'), bottom=Side(style='double', color='000000'))

    # --- SHEET 2: LOW STOCK ---
    ws_low = wb.create_sheet(title="Low Stock")
    ws_low.views.sheetView[0].showGridLines = True
    ws_low.merge_cells("A1:G2")
    title_cell = ws_low["A1"]
    title_cell.value = "  LOW STOCK REPLENISHMENT REQUIRED"
    title_cell.font = title_font
    title_cell.fill = PatternFill(start_color="F59E0B", end_color="F59E0B", fill_type="solid")
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_low["A3"] = f"Low stock alert status (Qty <= 5) - Generated: {now_str}"
    ws_low["A3"].font = meta_font

    ws_low.row_dimensions[4].height = 26
    for col_idx, header in enumerate(headers, 1):
        cell = ws_low.cell(row=4, column=col_idx)
        cell.value = header
        cell.font = white_font_bold
        cell.fill = PatternFill(start_color="D97706", end_color="D97706", fill_type="solid")
        cell.alignment = header_align
        cell.border = thin_border

    low_idx = 5
    for item in inventory_items:
        if 0 < item.quantity <= 5:
            ws_low.row_dimensions[low_idx].height = 20
            row_values = [
                item.id,
                item.name,
                item.sku,
                item.location_bin or "Main Aisle",
                item.quantity,
                f"{int(item.confidence * 100)}%" if item.confidence else "N/A",
                item.status
            ]
            for col_idx, val in enumerate(row_values, 1):
                cell = ws_low.cell(row=low_idx, column=col_idx)
                cell.value = val
                cell.font = normal_font
                cell.border = thin_border
                cell.fill = yellow_fill
                if col_idx in [1, 5, 6]:
                    cell.alignment = center_align
                else:
                    cell.alignment = left_align
            low_idx += 1

    # Auto-adjust column widths
    for ws in [ws_inv, ws_low]:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                if cell.row in [1, 2]:
                    continue
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    reports_dir = os.path.join(settings.LOCAL_STORAGE_DIR, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    file_name = f"store_report_{store_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    file_path = os.path.join(reports_dir, file_name)
    wb.save(file_path)
    file_url = f"/static/uploads/reports/{file_name}"

    report_record = ReportModel(
        store_id=store_id,
        generated_by_id=user_id,
        type="Excel",
        file_url=file_url,
        parameters={"generated_at": now_str, "scan_id": scan_id}
    )
    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    return file_url


@router.post("/store/{store_id}")
def generate_store_excel_report(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """API endpoint to generate Excel report."""
    try:
        file_url = generate_store_excel_report_internal(
            db=db,
            store_id=store_id,
            user_id=current_user.id
        )
        return {"file_url": file_url}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
