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
        self.configure(fg_color="#2b2b2b")  # Főablak háttér

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_patients_list())
        search_entry = ctk.CTkEntry(self, textvariable=self.search_var, placeholder_text="Keresés név vagy email szerint...")
        search_entry.pack(pady=10, padx=20, fill="x")

        self.patients_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.patients_frame.pack(pady=10, fill="both", expand=True)

        control_frame = ctk.CTkFrame(self, fg_color="#232323")
        control_frame.pack(pady=10)
        ctk.CTkButton(control_frame, text="Új páciens", command=self.open_edit_popup, fg_color="#205081", text_color="white").pack(side="left", padx=10)
        ctk.CTkButton(control_frame, text="Időpontok megtekintése", command=self.view_appointments, fg_color="#205081", text_color="white").pack(side="left", padx=10)
        ctk.CTkButton(control_frame, text="E heti időpontok", command=self.view_week_appointments, fg_color="#205081", text_color="white").pack(side="left", padx=10)

        self.refresh_patients_list()

    def refresh_patients_list(self):
        for widget in self.patients_frame.winfo_children():
            widget.destroy()

        query = self.search_var.get().lower()
        self.patients = [p for p in load_patients() if query in p["Név"].lower() or query in p["Email"].lower()]

        header = ctk.CTkFrame(self.patients_frame, fg_color="#232323")
        header.pack(fill="x", padx=10, pady=3)

        for text in ["Név", "E-mail", "Telefonszám"]:
            label = ctk.CTkLabel(header, text=text, anchor="w", width=250, fg_color="transparent", text_color="white", font=("Arial", 12, "bold"))
            label.pack(side="left", padx=(5, 10), fill="x", expand=False)

        for patient in self.patients:
            row = ctk.CTkFrame(self.patients_frame, fg_color="#232323")
            row.pack(fill="x", padx=10, pady=3)
            ctk.CTkLabel(row, text=patient['Név'], anchor="w", width=250, fg_color="transparent", text_color="white").pack(side="left", padx=(5, 10), fill="x", expand=False)
            ctk.CTkLabel(row, text=f"<{patient['Email']}>", anchor="w", width=250, fg_color="transparent", text_color="white").pack(side="left", padx=(5, 10), fill="x", expand=False)
            ctk.CTkLabel(row, text=f"(+{patient['Telefon']})", anchor="w", width=250, fg_color="transparent", text_color="white").pack(side="left", padx=(5, 10), fill="x", expand=False)
            ctk.CTkButton(row, text="PDF", width=60, command=lambda p=patient: export_patient_to_pdf(p), fg_color="#205081", text_color="white").pack(side="right", padx=5)
            ctk.CTkButton(row, text="Megnyitás", width=100, command=lambda p=patient: self.open_patient_detail(p), fg_color="#205081", text_color="white").pack(side="right", padx=5)


    #Az adott pácien adatlapjának megnyitása
    def open_patient_detail(self, patient):
        popup = ctk.CTkToplevel(self)
        popup.title(f"{patient['Név']} - Adatlap")
        popup.geometry("400x350")
        popup.focus()
        popup.grab_set()
        popup.resizable(False, False)
        popup.configure(fg_color="#2b2b2b")  # szürkés háttér

        for key, val in patient.items():
            ctk.CTkLabel(popup, text=f"{key}: {val}", fg_color="transparent", text_color="white").pack(pady=5)

        ctk.CTkButton(popup, text="Szerkesztés", command=lambda: [popup.destroy(), self.open_edit_popup(patient)], fg_color="#205081", text_color="white").pack(pady=5)
        ctk.CTkButton(popup, text="Törlés", fg_color="red", command=lambda: [popup.destroy(), self.delete_patient(patient)]).pack(pady=5)
        ctk.CTkButton(popup, text="Időpont foglalás", command=lambda: [popup.destroy(), self.book_appointment_popup()], fg_color="#205081", text_color="white").pack(pady=5)

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
        edit.configure(fg_color="#2b2b2b")  # szürkés háttér

        name_var = ctk.StringVar(value=patient["Név"] if patient else "")
        dob_var = ctk.StringVar(value=patient["Szul. dátum"] if patient else "")
        phone_var = ctk.StringVar(value=patient["Telefon"] if patient else "")
        email_var = ctk.StringVar(value=patient["Email"] if patient else "")

        for label, var in [("Név", name_var), ("Telefon", phone_var), ("Email", email_var)]:
            ctk.CTkLabel(edit, text=label, fg_color="transparent", text_color="white").pack()
            ctk.CTkEntry(edit, textvariable=var, width=250).pack(pady=5)

        ctk.CTkLabel(edit, text="Születési Dátum", fg_color="transparent", text_color="white").pack()
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
            
            #if not new_data["Név"].isalpha() or len(new_data["Név"]) < 2:
            #    messagebox.showerror("Hiba", "A név formátuma nem megfelelő!")
            #    return
            
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
<<<<<<< HEAD
            
            
            
=======
            if not new_data["Név"] or not new_data["Email"] or not new_data["Telefon"]:
                return
            if not new_data["Szul. dátum"]:
                messagebox.showerror("Hiba", "A születési dátum mező nem lehet üres!")
                return
                      
>>>>>>> origin/main
            data = [new_data if p["ID"] == new_data["ID"] else p for p in load_patients()]
            if not patient:
                data.append(new_data)
            save_all_patients(data)
            edit.destroy()
            self.refresh_patients_list()

        ctk.CTkButton(edit, text="Mentés", command=save).pack(pady=10)
<<<<<<< HEAD

    def book_appointment_popup(self, selected_patient=None):
        from datetime import timedelta

=======
        
    # Időpont foglalása
    def book_appointment(self, patient):
>>>>>>> origin/main
        book = ctk.CTkToplevel(self)
        book.geometry("1500x600")
        book.title("Időpont foglalás")
        book.focus()
        book.grab_set()
        book.resizable(False, False)
        book.configure(fg_color="#2b2b2b")

        # --- BAL: Naptár ---
        calendar_frame = ctk.CTkFrame(book, fg_color="#2b2b2b")
        calendar_frame.pack(side="left", fill="both", expand=True, padx=(20,10), pady=20)

        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        days = [(start_week + timedelta(days=i)) for i in range(7)]
        magyar_napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
        hours = [f"{h:02d}:00" for h in range(8, 20)]

        ctk.CTkLabel(calendar_frame, text="Válassz időpontot:", fg_color="transparent", text_color="white", font=("Arial", 16, "bold")).pack(pady=10)

        scroll_frame = ctk.CTkScrollableFrame(calendar_frame, fg_color="#2b2b2b", width=750, height=500)
        scroll_frame.pack(fill="both", expand=True)

        grid_frame = ctk.CTkFrame(scroll_frame, fg_color="#2b2b2b")
        grid_frame.pack(fill="both", expand=True)

        # Fejléc
        ctk.CTkLabel(grid_frame, text="", width=80, height=40, fg_color="transparent").grid(row=0, column=0, padx=2, pady=2)
        for col, d in enumerate(days):
            fejlec = f"{magyar_napok[col]}\n{d.strftime('%Y-%m-%d')}"
            ctk.CTkLabel(
                grid_frame,
                text=fejlec,
                font=("Arial", 12, "bold"),
                anchor="center",
                width=120,
                height=40,
                fg_color="#205081",
                corner_radius=8,
                text_color="white"
            ).grid(row=0, column=col+1, padx=2, pady=2, sticky="nsew")

        # Lefoglalt időpontok kigyűjtése
        appointments = load_appointments()
        booked = {(a["Dátum"], a["Időpont"]) for a in appointments}

        # Választott időpont változó
        selected_slot = {"day": None, "hour": None}

        def select_slot(day, hour):
            selected_slot["day"] = day
            selected_slot["hour"] = hour
            # Frissítsd a gombok színét, hogy látszódjon a kiválasztás
            for btn in slot_buttons.values():
                btn.configure(border_width=0)
            slot_buttons[(day.strftime("%Y-%m-%d"), hour)].configure(border_width=3, border_color="#FFD700")

        slot_buttons = {}
        for row, hour in enumerate(hours):
            ctk.CTkLabel(
                grid_frame,
                text=hour,
                font=("Arial", 11, "bold"),
                width=80,
                height=60,
                fg_color="#205081",
                text_color="white",
                anchor="center"
            ).grid(row=row+1, column=0, padx=2, pady=2, sticky="nsew")
            for col, day in enumerate(days):
                datum = day.strftime("%Y-%m-%d")
                is_booked = (datum, hour) in booked
                btn = ctk.CTkButton(
                    grid_frame,
                    text="Foglalt" if is_booked else "Szabad",
                    fg_color="#444444" if is_booked else "#22406a",
                    text_color="white",
                    state="disabled" if is_booked else "normal",
                    width=120,
                    height=60,
                    command=(lambda d=day, h=hour: select_slot(d, h)) if not is_booked else None
                )
                btn.grid(row=row+1, column=col+1, padx=2, pady=2, sticky="nsew")
                slot_buttons[(datum, hour)] = btn

        # --- JOBB: Páciens és megjegyzés ---
        side_frame = ctk.CTkFrame(book, fg_color="#232323", width=350)
        side_frame.pack(side="right", fill="y", padx=(10,20), pady=20)
        side_frame.pack_propagate(False)

        ctk.CTkLabel(side_frame, text="Páciens kiválasztása", fg_color="transparent", text_color="white", font=("Arial", 14, "bold")).pack(pady=(20,5))

        patients = load_patients()
        patient_names = [f"{p['Név']} ({p['Email']})" for p in patients]
        patient_var = ctk.StringVar(value=patient_names[0] if patient_names else "")

        # Keresőmező
        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(side_frame, textvariable=search_var, placeholder_text="Keresés név vagy email szerint...")
        search_entry.pack(pady=5, padx=10, fill="x")

        # Páciens ComboBox
        patient_combo = ctk.CTkComboBox(side_frame, values=patient_names, variable=patient_var, width=300)
        patient_combo.pack(pady=10)

        def update_combo(*_):
            query = search_var.get().lower()
            filtered = [f"{p['Név']} ({p['Email']})" for p in patients if query in p['Név'].lower() or query in p['Email'].lower()]
            patient_combo.configure(values=filtered)
            if filtered:
                patient_var.set(filtered[0])
            else:
                patient_var.set("")

        search_var.trace_add("write", update_combo)

        # Ha van kiválasztott páciens, tiltsd le a keresőt és comboboxot
        if selected_patient:
            selected_name = f"{selected_patient['Név']} ({selected_patient['Email']})"
            patient_var.set(selected_name)
            patient_combo.configure(state="disabled")
            search_entry.configure(state="disabled")

        # Megjegyzés
        ctk.CTkLabel(side_frame, text="Megjegyzés (opcionális):", fg_color="transparent", text_color="white").pack(pady=(20,5))
        megj_var = ctk.StringVar()
        ctk.CTkEntry(side_frame, textvariable=megj_var, width=300).pack(pady=5)

        # Foglalás gomb
        def on_book():
            # Páciens kiválasztása
            if selected_patient:
                selected_patient = selected_patient
            else:
                selected = patient_var.get()
                filtered = [p for p in patients if f"{p['Név']} ({p['Email']})" == selected]
                if not filtered:
                    messagebox.showerror("Hiba", "Nincs kiválasztott páciens!")
                    return
                selected_patient = filtered[0]
            # Időpont kiválasztása
            if not selected_slot["day"] or not selected_slot["hour"]:
                messagebox.showerror("Hiba", "Nincs kiválasztott időpont!")
                return
            # Mentés
            new_appt = {
                "ID": selected_patient.get("ID"),
                "Név": selected_patient.get("Név"),
                "Telefon": selected_patient.get("Telefon"),
                "Email": selected_patient.get("Email"),
                "Szul. dátum": selected_patient.get("Szul. dátum"),
                "Dátum": selected_slot["day"].strftime("%Y-%m-%d"),
                "Időpont": selected_slot["hour"],
                "Megjegyzés": megj_var.get()
            }
            save_appointment(new_appt)
            book.destroy()
            messagebox.showinfo("Siker", "Időpont lefoglalva!")

        ctk.CTkButton(side_frame, text="Időpont lefoglalása", command=on_book, fg_color="#205081", text_color="white", width=200, height=40).pack(pady=30)

    def view_appointments(self):
        appointments = load_appointments()

        win = ctk.CTkToplevel(self)
        win.title("Mai időpontok")
        win.geometry("600x500")
        win.focus()
        win.grab_set()
        win.resizable(False, False)
        win.configure(fg_color="#2b2b2b")  # szürkés háttér

        ctk.CTkLabel(win, text="Dátum kiválasztása", fg_color="transparent", text_color="white").pack(pady=5)
        native_frame = tkinter.Frame(win)
        native_frame.pack()
        date_picker = DateEntry(native_frame, date_pattern='yyyy-mm-dd', width=25)
        date_picker.pack()
        list_frame = ctk.CTkFrame(win, fg_color="#22406a")
        list_frame.pack(fill="both", expand=True, pady=10, padx=10)

        def refresh_list():
            for widget in list_frame.winfo_children():
                widget.destroy()
            selected_date = date_picker.get()
            daily_appts = [a for a in appointments if a["Dátum"] == selected_date]
            # Rendezés időpont szerint
            daily_appts = sorted(daily_appts, key=lambda a: a["Időpont"])
            if not daily_appts:
                ctk.CTkLabel(list_frame, text="Nincs időpont erre a napra.", fg_color="#183153", text_color="white").pack()
            else:
                for appt in daily_appts:
                    text = f"{appt['Időpont']} - {appt['Név']} ({appt['Megjegyzés']})"
                    ctk.CTkLabel(list_frame, text=text, fg_color="#183153", text_color="white").pack(anchor="w", pady=2)

        ctk.CTkButton(win, text="Mutasd az időpontokat", command=refresh_list, fg_color="#205081", text_color="white").pack(pady=10)

    def view_week_appointments(self):
        appointments = load_appointments()
        current_week_offset = [0]  # Listában, hogy closure-ból módosítható legyen

        win = ctk.CTkToplevel(self)
        win.title("Időpontok megtekintése - Hét")
        win.geometry("1100x500")
        win.focus()
        win.grab_set()
        win.resizable(False, False)
        win.configure(fg_color="#2b2b2b")  # szürkés háttér

        nav_frame = ctk.CTkFrame(win, fg_color="#2b2b2b")
        nav_frame.pack(pady=5)

        list_frame = ctk.CTkFrame(win, fg_color="#2b2b2b")
        list_frame.pack(fill="both", expand=True, pady=10, padx=10)

        def refresh_week_list():
            for widget in list_frame.winfo_children():
                widget.destroy()
            today = date.today()
            start_week = today - timedelta(days=today.weekday()) + timedelta(weeks=current_week_offset[0])
            end_week = start_week + timedelta(days=6)
            ctk.CTkLabel(list_frame, text=f"Hét: {start_week} - {end_week}", font=("Arial", 16, "bold"), fg_color="transparent", text_color="white").pack(pady=5)

            magyar_napok = ["Hétfő", "Kedd", "Szerda", "Csütörtök", "Péntek", "Szombat", "Vasárnap"]
            days = [(start_week + timedelta(days=i)) for i in range(7)]
            day_keys = [d.strftime("%Y-%m-%d") for d in days]

            # Időpontok kigyűjtése és rendezése
            all_times = set()
            appt_map = {day: {} for day in day_keys}
            for a in appointments:
                try:
                    appt_date = datetime.strptime(a['Dátum'], "%Y-%m-%d").date()
                    key = appt_date.strftime("%Y-%m-%d")
                    if key in appt_map:
                        appt_map[key][a['Időpont']] = a
                        all_times.add(a['Időpont'])
                except Exception:
                    continue
            sorted_times = sorted(all_times)

            # Grid frame
            grid_frame = ctk.CTkFrame(list_frame, fg_color="#2b2b2b")
            grid_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Fejléc: első cella üres, utána napok
            ctk.CTkLabel(grid_frame, text="", width=80, height=40, fg_color="transparent").grid(row=0, column=0, padx=2, pady=2)
            for col, d in enumerate(days):
                fejlec = f"{magyar_napok[col]}\n{d.strftime('%Y-%m-%d')}"
                lbl = ctk.CTkLabel(
                    grid_frame,
                    text=fejlec,
                    font=("Arial", 12, "bold"),
                    anchor="center",
                    width=120,
                    height=40,
                    fg_color="#205081",
                    corner_radius=8,
                    text_color="white"
                )
                lbl.grid(row=0, column=col+1, padx=2, pady=2, sticky="nsew")

            # Sorok: időpont + napok
            for row, time in enumerate(sorted_times):
                # Időpont oszlop
                ctk.CTkLabel(
                    grid_frame,
                    text=time,
                    font=("Arial", 11, "bold"),
                    width=80,
                    height=60,
                    fg_color="#205081",
                    text_color="white",
                    anchor="center"
                ).grid(row=row+1, column=0, padx=2, pady=2, sticky="nsew")
                # Napok oszlopai
                for col, day in enumerate(day_keys):
                    a = appt_map[day].get(time)
                    text = f"{a['Név']}\n({a['Megjegyzés']})" if a else ""
                    cell_frame = ctk.CTkFrame(
                        grid_frame,
                        fg_color="#22406a" if a else "#205081",
                        corner_radius=8,
                        width=120,
                        height=90
                    )
                    cell_frame.grid(row=row+1, column=col+1, padx=2, pady=2, sticky="nsew")
                    cell_label = ctk.CTkLabel(
                        cell_frame,
                        text=text,
                        anchor="nw",
                        justify="left",
                        font=("Arial", 11),
                        text_color="white",
                        fg_color="transparent"
                    )
                    cell_label.pack(fill="both", expand=True, padx=4, pady=8)

                    # Részletek gomb csak ha van időpont
                    if a:
                        details_btn = ctk.CTkButton(
                            cell_frame,
                            text="Részletek",
                            width=80,
                            height=28,
                            font=("Arial", 10),
                            fg_color="#2a5a9e",
                            text_color="white",
                            command=lambda appt=a: open_details_window(appt)
                        )
                        details_btn.place(relx=0.5, rely=0.5, anchor="center")
                        details_btn.place_forget()

                        hover_count = {"count": 0}

                        def on_enter(e, btn=details_btn):
                            hover_count["count"] += 1
                            btn.place(relx=0.5, rely=0.5, anchor="center")
                        def on_leave(e, btn=details_btn):
                            hover_count["count"] -= 1
                            if hover_count["count"] <= 0:
                                btn.place_forget()

                        for widget in (cell_frame, cell_label, details_btn):
                            widget.bind("<Enter>", on_enter)
                            widget.bind("<Leave>", on_leave)

        def prev_week():
            current_week_offset[0] -= 1
            refresh_week_list()

        def next_week():
            current_week_offset[0] += 1
            refresh_week_list()

        ctk.CTkButton(nav_frame, text="<< Előző hét", command=prev_week, fg_color="#205081", text_color="white").pack(side="left", padx=10)
        ctk.CTkButton(nav_frame, text="Következő hét >>", command=next_week, fg_color="#205081", text_color="white").pack(side="left", padx=10)
        ctk.CTkButton(nav_frame, text="Frissítés", command=refresh_week_list, fg_color="#205081", text_color="white").pack(side="left", padx=10)
        ctk.CTkButton(
            nav_frame,
            text="Új időpont foglalása",
            fg_color="#22406a",
            text_color="white",
            command=lambda: self.book_appointment_popup()
        ).pack(side="left", padx=10)

        refresh_week_list()

        # Új ablak a részletekhez
        def open_details_window(appt):
            detail_win = ctk.CTkToplevel(win)
            detail_win.title(f"Részletek - {appt['Név']} ({appt['Dátum']} {appt['Időpont']})")
            detail_win.geometry("400x350")
            detail_win.focus()
            detail_win.grab_set()
            detail_win.configure(fg_color="#2b2b2b")  # sötétszürke háttér

            ctk.CTkLabel(detail_win, text=f"Név: {appt['Név']}", text_color="white", fg_color="transparent").pack(pady=5)
            ctk.CTkLabel(detail_win, text=f"Dátum: {appt['Dátum']}", text_color="white", fg_color="transparent").pack(pady=5)
            ctk.CTkLabel(detail_win, text=f"Időpont: {appt['Időpont']}", text_color="white", fg_color="transparent").pack(pady=5)
            ctk.CTkLabel(detail_win, text=f"Megjegyzés: {appt['Megjegyzés']}", text_color="white", fg_color="transparent").pack(pady=5)

            # Olaj kiválasztása
            olaj_lista = ["Levendula", "Eukaliptusz", "Narancs", "Kókusz", "Teafa"]
            ctk.CTkLabel(detail_win, text="Használt olaj:", text_color="white", fg_color="transparent").pack(pady=(10, 2))
            olaj_var = ctk.StringVar(value=olaj_lista[0])
            olaj_combo = ctk.CTkComboBox(detail_win, values=olaj_lista, variable=olaj_var, width=200)
            olaj_combo.pack(pady=2)

            ctk.CTkLabel(detail_win, text="Kezelés részletei:", text_color="white", fg_color="transparent").pack(pady=5)
            details_box = ctk.CTkTextbox(detail_win, width=300, height=100)
            details_box.pack(pady=5)
            ctk.CTkButton(detail_win, text="Mentés", command=detail_win.destroy, fg_color="#205081", text_color="white").pack(pady=10)

    def select_patient_and_book(self):
        select_win = ctk.CTkToplevel(self)
        select_win.title("Páciens kiválasztása")
        select_win.geometry("400x400")
        select_win.focus()
        select_win.grab_set()
        select_win.configure(fg_color="#2b2b2b")

        ctk.CTkLabel(select_win, text="Válassz pácienst:", fg_color="transparent", text_color="white").pack(pady=10)

        patients = load_patients()
        patient_names = [f"{p['Név']} ({p['Email']})" for p in patients]
        patient_var = ctk.StringVar(value=patient_names[0] if patient_names else "")

        # Keresőmező
        search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(select_win, textvariable=search_var, placeholder_text="Keresés név vagy email szerint...")
        search_entry.pack(pady=5, padx=10, fill="x")

        # ComboBox
        patient_combo = ctk.CTkComboBox(select_win, values=patient_names, variable=patient_var, width=300)
        patient_combo.pack(pady=10)

        def update_combo(*_):
            query = search_var.get().lower()
            filtered = [f"{p['Név']} ({p['Email']})" for p in patients if query in p['Név'].lower() or query in p['Email'].lower()]
            patient_combo.configure(values=filtered)
            if filtered:
                patient_var.set(filtered[0])
            else:
                patient_var.set("")

        search_var.trace_add("write", update_combo)

        def on_select():
            selected = patient_var.get()
            filtered = [p for p in patients if f"{p['Név']} ({p['Email']})" == selected]
            if not filtered:
                return
            patient = filtered[0]
            select_win.destroy()
            self.book_appointment(patient)

        ctk.CTkButton(select_win, text="Kiválaszt", command=on_select, fg_color="#205081", text_color="white").pack(pady=10)
