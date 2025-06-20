import tkinter
import customtkinter as ctk
from openpyxl import Workbook, load_workbook
import os
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime, date, timedelta
from tkcalendar import DateEntry
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
import tkinter.messagebox as messagebox

from date_handler import load_patients, save_all_patients, save_to_excel
from appointments import save_appointment, load_appointments
from pdf_export import export_patient_to_pdf

class App(ctk.CTk):

    # Főmenü
    def __init__(self):
        super().__init__()
        self.title("Masszőr Program")
        self.geometry("1000x700")
        self.resizable(False, False)

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_patients_list())
        search_entry = ctk.CTkEntry(self, textvariable=self.search_var, placeholder_text="Keresés név vagy email szerint...")
        search_entry.pack(pady=10, padx=20, fill="x")

        self.patients_frame = ctk.CTkFrame(self)
        self.patients_frame.pack(pady=10, fill="both", expand=True)

        control_frame = ctk.CTkFrame(self)
        control_frame.pack(pady=10)
        ctk.CTkButton(control_frame, text="Új páciens", command=self.open_edit_popup).pack(side="left", padx=10)
        ctk.CTkButton(control_frame, text="Időpontok megtekintése", command=self.view_appointments).pack(side="left", padx=10)
        ctk.CTkButton(control_frame, text="E heti időpontok", command=self.view_week_appointments).pack(side="left", padx=10)

        self.refresh_patients_list()

    def refresh_patients_list(self):
        for widget in self.patients_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().lower()
        self.patients = [p for p in load_patients() if query in p["Név"].lower() or query in p["Email"].lower()]

        header = ctk.CTkFrame(self.patients_frame)
        header.pack(fill="x", padx=10, pady=3)

        for text in ["Név", "E-mail", "Telefonszám"]:
            label = ctk.CTkLabel(header, text=text, anchor="w", width=250)
            label.pack(side="left", padx=(5, 10), fill="x", expand=False)

        for patient in self.patients:
            row = ctk.CTkFrame(self.patients_frame)
            row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(row, text=patient['Név'], anchor="w", width=250).pack(side="left", padx=(5, 10), fill="x", expand=False)
            ctk.CTkLabel(row, text=f"<{patient['Email']}>", anchor="w", width=250).pack(side="left", padx=(5, 10), fill="x", expand=False)
            ctk.CTkLabel(row, text=f"(+{patient['Telefon']})", anchor="w", width=250).pack(side="left", padx=(5, 10), fill="x", expand=False)
            ctk.CTkButton(row, text="PDF", width=60, command=lambda p=patient: export_patient_to_pdf(p)).pack(side="right", padx=5)
            ctk.CTkButton(row, text="Megnyitás", width=100, command=lambda p=patient: self.open_patient_detail(p)).pack(side="right", padx=5)


    #Az adott pácien adatlapjának megnyitása
    def open_patient_detail(self, patient):
        popup = ctk.CTkToplevel(self)
        popup.title(f"{patient['Név']} - Adatlap")
        popup.geometry("400x350")
        popup.focus()
        popup.grab_set()
        popup.resizable(False, False)

        for key, val in patient.items():
            ctk.CTkLabel(popup, text=f"{key}: {val}").pack(pady=5)

        ctk.CTkButton(popup, text="Szerkesztés", command=lambda: [popup.destroy(), self.open_edit_popup(patient)]).pack(pady=5)
        ctk.CTkButton(popup, text="Törlés", fg_color="red", command=lambda: [popup.destroy(), self.delete_patient(patient)]).pack(pady=5)
        ctk.CTkButton(popup, text="Időpont foglalás", command=lambda: [popup.destroy(), self.book_appointment(patient)]).pack(pady=5)

    # Páciensek törlése
    def delete_patient(self, patient):
        self.patients = [p for p in load_patients() if p["ID"] != patient["ID"]]
        save_all_patients(self.patients)
        self.refresh_patients_list()

    #Az adott páciens szerkesztése vagy új páciens hozzáadása
    def open_edit_popup(self, patient=None):
        edit = ctk.CTkToplevel(self)
        edit.geometry("400x400")
        edit.title("Páciens szerkesztése" if patient else "Új páciens")
        edit.focus()
        edit.grab_set()
        edit.resizable(False, False)

        name_var = ctk.StringVar(value=patient["Név"] if patient else "")
        dob_var = ctk.StringVar(value=patient["Szul. dátum"] if patient else "")
        phone_var = ctk.StringVar(value=patient["Telefon"] if patient else "")
        email_var = ctk.StringVar(value=patient["Email"] if patient else "")

        for label, var in [("Név", name_var), ("Telefon", phone_var), ("Email", email_var)]:
            ctk.CTkLabel(edit, text=label).pack()
            ctk.CTkEntry(edit, textvariable=var, width=250).pack(pady=5)

        ctk.CTkLabel(edit, text="Születési Dátum").pack()
        native_frame = tkinter.Frame(edit)
        native_frame.pack()
        date_entry = DateEntry(native_frame, date_pattern='yyyy-mm-dd', width=25)
        date_entry.pack()
        dob_var = date_entry

        def save():
            new_data = {
                "ID": patient["ID"] if patient else str(uuid.uuid4()),
                "Név": name_var.get(),
                "Telefon": phone_var.get(),
                "Email": email_var.get(),
                "Szul. dátum": dob_var.get()
            }

            if new_data["Név"] == "":
                messagebox.showerror("Hiba", "A név mező nem lehet üres!")
                return
            if not new_data["Név"].isalpha() or len(new_data["Név"]) < 2:
                messagebox.showerror("Hiba", "A név formátuma nem megfelelő!")
                return
            
            if new_data["Telefon"] == "":
                messagebox.showerror("Hiba", "A telefon mező nem lehet üres!")
                return
            if not new_data["Telefon"].isdigit() or len(new_data["Telefon"]) < 8:
                messagebox.showerror("Hiba", "A telefon formátuma nem megfelelő!")
                return
            
            if new_data["Email"] == "":
                messagebox.showerror("Hiba", "Az email mező nem lehet üres!")
                return
            if not new_data["Email"].count("@") == 1 or not new_data["Email"].count(".") >= 1:
                messagebox.showerror("Hiba", "Az email formátuma nem megfelelő!")
                return
            
            if new_data["Szul. dátum"] == "":
                messagebox.showerror("Hiba", "A születési dátum mező nem lehet üres!")
                return
            if not new_data["Név"] or not new_data["Email"] or not new_data["Telefon"]:
                return
            if not new_data["Szul. dátum"]:
                messagebox.showerror("Hiba", "A születési dátum mező nem lehet üres!")
                return
                      
            data = [new_data if p["ID"] == new_data["ID"] else p for p in load_patients()]
            if not patient:
                data.append(new_data)
            save_all_patients(data)
            edit.destroy()
            self.refresh_patients_list()

        ctk.CTkButton(edit, text="Mentés", command=save).pack(pady=10)
        
    # Időpont foglalása
    def book_appointment(self, patient):
        book = ctk.CTkToplevel(self)
        book.geometry("600x400")
        book.title("Időpont foglalás")
        book.focus()
        book.grab_set()
        book.resizable(False, False)

        ctk.CTkLabel(book, text="Dátum").pack()
        native_frame = tkinter.Frame(book)
        native_frame.pack()
        date_entry = DateEntry(native_frame, date_pattern='yyyy-mm-dd', mindate=date.today(), width=25)
        date_entry.pack()

        ctk.CTkLabel(book, text="Időpont").pack()
        time_var = ctk.StringVar()
        time_combo = ttk.Combobox(book, textvariable=time_var, width=25)
        time_combo['values'] = [f"{h:02d}:00" for h in range(8, 20)]
        time_combo.current(0)
        time_combo.pack(pady=5)

        ctk.CTkLabel(book, text="Megjegyzés").pack()
        note_box = ctk.CTkTextbox(book, width=250, height=100)
        note_box.pack(pady=5)

        def save_appt():
            save_appointment(patient["ID"], patient["Név"], date_entry.get(), time_var.get(), note_box.get("1.0", "end-1c"))
            book.destroy()

        ctk.CTkButton(book, text="Foglalás mentése", command=save_appt).pack(pady=10)

    def view_appointments(self):
        appointments = load_appointments()

        win = ctk.CTkToplevel(self)
        win.title("Időpontok megtekintése")
        win.geometry("600x500")
        win.focus()
        win.grab_set()
        win.resizable(False, False)

        ctk.CTkLabel(win, text="Dátum kiválasztása").pack(pady=5)
        native_frame2 = tkinter.Frame(win)
        native_frame2.pack()
        date_picker = DateEntry(native_frame2, date_pattern='yyyy-mm-dd', mindate=date.today())
        date_picker.pack()

        list_frame = ctk.CTkFrame(win)
        list_frame.pack(fill="both", expand=True, pady=10, padx=10)

        def refresh_list():
            for widget in list_frame.winfo_children():
                widget.destroy()
            selected_date = date_picker.get()
            daily_appts = [a for a in appointments if a["Dátum"] == selected_date]
            if not daily_appts:
                ctk.CTkLabel(list_frame, text="Nincs időpont erre a napra.").pack()
            else:
                for appt in daily_appts:
                    text = f"{appt['Időpont']} - {appt['Név']} ({appt['Megjegyzés']})"
                    ctk.CTkLabel(list_frame, text=text).pack(anchor="w", pady=2)

        ctk.CTkButton(win, text="Mutasd az időpontokat", command=refresh_list).pack(pady=10)

    def view_week_appointments(self):
        appointments = load_appointments()
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)

        win = ctk.CTkToplevel(self)
        win.title("E heti időpontok")
        win.geometry("600x500")
        win.focus()
        win.grab_set()
        win.resizable(False, False)

        list_frame = ctk.CTkFrame(win)
        list_frame.pack(fill="both", expand=True, pady=10, padx=10)

        week_appts = [a for a in appointments if start_week <= datetime.strptime(a['Dátum'], "%Y-%m-%d").date() <= end_week]
        if not week_appts:
            ctk.CTkLabel(list_frame, text="Nincs időpont erre a hétre.").pack()
        else:
            for appt in sorted(week_appts, key=lambda a: (a['Dátum'], a['Időpont'])):
                text = f"{appt['Dátum']} {appt['Időpont']} - {appt['Név']} ({appt['Megjegyzés']})"
                ctk.CTkLabel(list_frame, text=text).pack(anchor="w", pady=2)

if __name__ == "__main__":
    ctk.set_default_color_theme("dark-blue")
    ctk.set_appearance_mode("system")
    app = App()
    app.mainloop()
