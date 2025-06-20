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
from appointments import save_appointment, load_appointments
from appointments import load_appointments
from date_handler import load_patients, save_all_patients, save_to_excel

FILENAME = "data/adatok.xlsx"
APPOINTMENT_FILE = "data/idopontok.xlsx"

def export_patient_to_pdf(patient):
    from appointments import load_appointments
    default_filename = f"{patient['Név'].replace(' ', '_')}_export.pdf"
    filename = asksaveasfilename(defaultextension=".pdf", initialfile=default_filename, filetypes=[("PDF files", "*.pdf")])
    if not filename:
        return

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Páciens adatai")
    y -= 30

    c.setFont("Helvetica", 12)
    for key in ["Név", "Telefon", "Email", "Szul. dátum"]:
        c.drawString(50, y, f"{key}: {patient.get(key, '')}")
        y -= 20

    # Időpontok kigyűjtése
    appointments = load_appointments()
    patient_appts = [a for a in appointments if a.get("Név") == patient.get("Név")]

    y -= 10
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Időpontok:")
    y -= 25

    c.setFont("Helvetica", 12)
    if not patient_appts:
        c.drawString(60, y, "Nincs időpont.")
        y -= 20
    else:
        for appt in sorted(patient_appts, key=lambda a: (a["Dátum"], a["Időpont"])):
            c.drawString(60, y, f"{appt['Dátum']} {appt['Időpont']} - {appt.get('Megjegyzés', '')}")
            y -= 18
            if y < 60:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 12)

    c.save()

    # Ellenőrzéshez: printeld ki az ID-kat
    print("Páciens ID:", repr(patient.get("ID")))
    for a in appointments:
        print("Időpont ID:", repr(a.get("ID")), "Név:", a.get("Név"))
