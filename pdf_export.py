import tkinter
import customtkinter as ctk
from openpyxl import Workbook, load_workbook
import os
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime, date
from tkcalendar import DateEntry
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
from tkinter import ttk

def export_patient_to_pdf(patient):
    default_filename = f"{patient['Név'].replace(' ', '_')}_export.pdf"
    filename = asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF fájlok", "*.pdf")], initialfile=default_filename)
    if not filename:
        return
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Páciens adatlap: {patient['Név']}")
    y -= 30
    c.setFont("Helvetica", 10)
    for line in [
        f"Név: {patient['Név']}",
        f"Email: {patient['Email']}",
        f"Születési dátum: {patient['Szul. dátum']}",
        f"Telefon: {patient['Telefon']}",
        f"ID: {patient['ID']}"
    ]:
        c.drawString(50, y, line)
        y -= 15
    c.save()
