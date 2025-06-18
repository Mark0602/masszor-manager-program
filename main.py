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
from app import App
from date_handler import load_patients, save_all_patients, save_to_excel

FILENAME = "data/adatok.xlsx"
APPOINTMENT_FILE = "data/idopontok.xlsx"




if __name__ == "__main__":
    ctk.set_default_color_theme("dark-blue")
    ctk.set_appearance_mode("system")
    app = App()
    app.mainloop()
