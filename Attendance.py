import tkinter as tk
from tkinter import ttk, messagebox, font
from PIL import Image, ImageTk
import sqlite3
import os
import sys
import csv

def get_database_path(db_name):
    """ Get the path for the database file. """
    return os.path.join(os.getcwd(), db_name)

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()

        if os.path.exists(resource_path("logo.ico")):
            self.iconbitmap(resource_path("logo.ico"))
        else:
            print(f"Warning: {resource_path("logo.ico")} not found.")

        self.title('SCA Event Handler')
        self.geometry('1440x720')

        custom_font = font.Font(family='Century Gothic', size=10)
        style = ttk.Style(self)
        style.configure('.', font=custom_font)
        style.configure('Treeview', font=custom_font)

        style.configure('Treeview',
                        background='white',  # Background color of rows
                        foreground='black',  # Text color of rows
                        fieldbackground='lightgrey',
                        borderwidth=0)  # Background color of the field
                         
        style.configure('Treeview.Heading',
                        background='grey',  # Background color of headers
                        foreground='black',  # Text color of headers
                        font=('Century Gothic', 10),
                        borderwidth=0)  

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.merged_tab = ttk.Frame(self.notebook)
        self.initMergedTab()

        self.rfid_tab = ttk.Frame(self.notebook)
        self.initRFIDTab()

        self.notebook.add(self.rfid_tab, text='Attendance')
        self.notebook.add(self.merged_tab, text='Manage Data')

        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_change)

    def on_tab_change(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        
        if selected_tab == 'Manage Data':
            self.refresh_manage_data_tab()

    def refresh_manage_data_tab(self):
        self.refresh_database_list()  
        self.table.delete(*self.table.get_children())  
        self.load_data()  


    def initMergedTab(self):
        paned_window = ttk.PanedWindow(self.merged_tab, orient=tk.HORIZONTAL)
        paned_window.pack(expand=True, fill=tk.BOTH)

        input_frame = ttk.Frame(paned_window)
        paned_window.add(input_frame)

        self.initInputData(input_frame)

        view_frame = ttk.Frame(paned_window)
        paned_window.add(view_frame, weight=1)

        database_frame = ttk.LabelFrame(view_frame, text='Database Controls')
        database_frame.pack(padx=20, pady=20, fill=tk.X)

        self.database_selector_manage = ttk.Combobox(database_frame, width=30)
        self.database_selector_manage.pack(side=tk.LEFT, padx=5, pady=15)
        self.database_selector_manage.bind('<<ComboboxSelected>>', self.on_database_change)

        sort_button = ttk.Button(database_frame, text='Sort', command=self.sort_by_year_level)
        sort_button.pack(side=tk.LEFT, padx=5, pady=15)

        refresh_button = ttk.Button(database_frame, text='Refresh Table', command=self.load_data)
        refresh_button.pack(side=tk.LEFT, padx=5, pady=15)

        delete_button = ttk.Button(database_frame, text='Delete', command=self.delete_data)
        delete_button.pack(side=tk.LEFT, padx=5, pady=15)

        export_button = ttk.Button(database_frame, text='Export', command=self.export_data_to_file)
        export_button.pack(side=tk.LEFT, padx=5, pady=15)

        create_db_label = ttk.Label(database_frame, text='New DB Name:')
        create_db_label.pack(side=tk.LEFT, padx=5, pady=15)

        self.new_db_name_entry = ttk.Entry(database_frame, width=20)
        self.new_db_name_entry.pack(side=tk.LEFT, padx=5, pady=15)

        create_db_button = ttk.Button(database_frame, text='Create', command=self.create_db_button_clicked)
        create_db_button.pack(side=tk.LEFT, padx=5, pady=15)

        delete_db_button = ttk.Button(database_frame, text='Delete DB', command=self.delete_database_button_clicked)
        delete_db_button.pack(side=tk.LEFT, padx=5, pady=15)

        self.table = ttk.Treeview(view_frame, columns=('ID', 'Student ID#', 'Name', 'Year Level', 'RFID'), show='headings')
        self.table.pack(padx=20, pady=(0, 20), fill=tk.BOTH, expand=True)

        self.table.heading('ID', text='#')
        self.table.heading('Student ID#', text='Student ID#')
        self.table.heading('Name', text='Name')
        self.table.heading('Year Level', text='Year Level')
        self.table.heading('RFID', text='RFID')

        self.table.column('ID', width=50)          
        self.table.column('Student ID#', width=100)  
        self.table.column('Name', width=250)      
        self.table.column('Year Level', width=50) 
        self.table.column('RFID', width=150)       

        self.table.bind("<Double-1>", self.on_row_double_click)

    def on_database_change(self, event):
        selected_database = self.database_selector_manage.get()
        self.load_data()
        self.update_db_info_tree(selected_database)

    def update_db_info_tree(self, selected_database):
        self.db_info_tree.delete(*self.db_info_tree.get_children())

        if not selected_database:
            return

        db_path = get_database_path(selected_database)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM students''') 
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                self.db_info_tree.insert('', 'end', values=row)

        except Exception as e:
            messagebox.showerror('Database Error', str(e))

    def on_row_double_click(self, event):
        item = self.table.selection()[0]
        row_data = self.table.item(item, 'values')
        self.edit_id = row_data[0]  

        self.studentID_input.delete(0, tk.END)
        self.studentID_input.insert(0, row_data[1])

        self.name_input.delete(0, tk.END)
        self.name_input.insert(0, row_data[2])

        self.year_level_input.delete(0, tk.END)
        self.year_level_input.insert(0, row_data[3])

        self.rfid_input.delete(0, tk.END)
        self.rfid_input.insert(0, row_data[4])

    def search_data(self):
        search_term = self.search_entry.get().strip()

        if not search_term:
            messagebox.showwarning('Input Error', 'Please enter a search term.')
            return

        try:
            conn = sqlite3.connect(resource_path("SCA.db"))
            cursor = conn.cursor()
            
            query = '''
                SELECT * FROM students 
                WHERE rfid LIKE ? 
                OR studentID LIKE ? 
                OR name LIKE ? 
                OR year_level LIKE ?
            '''
            parameters = (
                f'%{search_term}%', 
                f'%{search_term}%', 
                f'%{search_term}%', 
                f'%{search_term}%'
            )
            
            cursor.execute(query, parameters)
            result = cursor.fetchall()
            conn.close()

            self.table.delete(*self.table.get_children())

            if not result:
                messagebox.showinfo('Search Result', 'No matching records found.')
            
            for row in result:
                self.table.insert('', 'end', values=row)

            self.highlight_search_results(search_term)

        except sqlite3.Error as e:
            messagebox.showerror('Database Error', f'An error occurred while searching: {e}')

    def highlight_search_results(self, search_term):
        search_term_lower = search_term.lower()
        for item in self.table.get_children():
            row_values = self.table.item(item, 'values')
            if any(search_term_lower in str(value).lower() for value in row_values):
                self.table.item(item, tags='highlight')
            else:
                self.table.item(item, tags='')

        self.table.tag_configure('highlight', background='cyan')


    def initInputData(self, parent):
        ttk.Label(parent, text='', width=2).grid(row=1, column=0, columnspan=2, pady=(0, 10))
        ttk.Label(parent, text='', width=2).grid(row=2, column=0, columnspan=2, )

        ttk.Label(parent, text='Select Event').grid(row=3, column=0, padx=10, pady=5)

        self.database_selector_attendance = ttk.Combobox(parent, width=28)
        self.database_selector_attendance.grid(row=3, column=1, padx=18, pady=5)

        refreshDB_button = ttk.Button(parent, text='Refresh DB', command=self.refresh_database_list)
        refreshDB_button.grid(row=4, columnspan=4, pady=10)

        ttk.Label(parent, text='', width=2).grid(row=5, column=0, columnspan=2, )

        ttk.Label(parent, text='Registration Section').grid(row=6, columnspan=2, padx=10, pady=5)

        ttk.Label(parent, text='Student ID#').grid(row=7, column=0, padx=10, pady=5)
        self.studentID_input = ttk.Entry(parent, width=30)
        self.studentID_input.grid(row=7, column=1, padx=10, pady=5)

        ttk.Label(parent, text='Full Name').grid(row=8, column=0, padx=10, pady=5)
        self.name_input = ttk.Entry(parent, width=30)
        self.name_input.grid(row=8, column=1, padx=10, pady=5)

        ttk.Label(parent, text='Year Level').grid(row=9, column=0, padx=10, pady=5)
        self.year_level_input = ttk.Entry(parent, width=30)
        self.year_level_input.grid(row=9, column=1, padx=10, pady=5)

        ttk.Label(parent, text='RFID').grid(row=10, column=0, padx=10, pady=5)
        self.rfid_input = ttk.Entry(parent, width=30)
        self.rfid_input.grid(row=10, column=1, padx=10, pady=5)

        submit_button = ttk.Button(parent, text='Submit', command=self.submit_data)
        submit_button.grid(row=11, columnspan=3, pady=10)

        ttk.Label(parent, text='Search:').grid(row=12, column=0, padx=10, pady=5)
        self.search_entry = ttk.Entry(parent, width=30)
        self.search_entry.grid(row=12, column=1, padx=10, pady=5)

        search_button = ttk.Button(parent, text='Find', command=self.search_data)
        search_button.grid(row=13, columnspan=3, pady=10)

    def initRFIDTab(self):
        frame = ttk.Frame(self.rfid_tab)
        frame.pack(expand=True, fill=tk.BOTH)

        self.canvas = tk.Canvas(frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        try:
            image = Image.open(resource_path("RFID_bg.png"))
            resized_image = image.resize((1440, 720))
            self.image = ImageTk.PhotoImage(resized_image)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image)
        except FileNotFoundError:
            print(f"Warning: {resource_path('RFID_bg.png')} not found.")

        self.scan_status_label = tk.Label(self.canvas, text='', font=("Century Gothic", 35), bg='white')
        self.canvas.create_window(350, 260, window=self.scan_status_label)  

        self.rfid_scanner_input = tk.Entry(self.canvas, width=14, font=("Century Gothic", 60))
        self.rfid_scanner_input.pack(side=tk.LEFT, padx=20, pady=20)
        self.canvas.create_window(352, 102, window=self.rfid_scanner_input)  
        self.rfid_scanner_input.config(bg='white', highlightthickness=0, highlightbackground='white')
        self.rfid_scanner_input.bind('<Return>', lambda event: self.auto_insert_data())

        self.db_info_tree = ttk.Treeview(self.canvas, columns=('Column1', 'Column2', 'Column3', 'Column4'), show='headings')
        self.db_info_tree.heading('Column1', text='#')
        self.db_info_tree.heading('Column2', text='Student ID')
        self.db_info_tree.heading('Column3', text='Name')
        self.db_info_tree.heading('Column4', text='Year')

        self.db_info_tree.pack(side=tk.RIGHT, padx=20, pady=20)
        self.canvas.create_window(734, 53, window=self.db_info_tree, anchor='nw')

        num_rows = 27
        row_height = 55  
        self.db_info_tree.config(height=num_rows)

        self.db_info_tree.column('Column1', width=55)
        self.db_info_tree.column('Column2', width=140)
        self.db_info_tree.column('Column3', width=360)
        self.db_info_tree.column('Column4', width=105)

    def update_table(self):
        for item in self.db_info_tree.get_children():
            self.db_info_tree.delete(item)

        try:
            db_path = resource_path(self.database_selector_manage.get())
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM students''')
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                self.db_info_tree.insert('', tk.END, values=row)

            if rows:
                self.db_info_tree.yview_moveto(1)

                latest_entry_id = self.db_info_tree.get_children()[-1]
                self.db_info_tree.item(latest_entry_id, tags=('highlight',))
                self.db_info_tree.tag_configure('highlight', background='yellow')

                self.after(2000, self.remove_highlight, latest_entry_id)

        except Exception as e:
            messagebox.showerror('Database Error', str(e))

    def remove_highlight(self, item_id):
        self.db_info_tree.item(item_id, tags=())

    def display_scan_status(self, text):
        self.scan_status_label.config(text=text)
        self.after(2000, lambda: self.scan_status_label.config(text=''))

    def submit_data(self):
        studentID = self.studentID_input.get()
        name = self.name_input.get()
        year_level = self.year_level_input.get()
        rfid = self.rfid_input.get()

        if not studentID or not name or not year_level or not rfid:
            messagebox.showwarning('Input Error', 'All fields are required.')
            return

        try:
            conn = sqlite3.connect(resource_path("SCA.db"))
            cursor = conn.cursor()
            if hasattr(self, 'edit_id') and self.edit_id:
                cursor.execute('''UPDATE students SET studentID=?, name=?, year_level=?, rfid=? WHERE id=?''',
                            (studentID, name, year_level, rfid, self.edit_id))
                del self.edit_id
            else:
                cursor.execute('''INSERT INTO students (studentID, name, year_level, rfid) VALUES (?, ?, ?, ?)''',
                            (studentID, name, year_level, rfid))

            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror('Database Error', str(e))
        finally:
            conn.close()

        messagebox.showinfo('Success', 'Data submitted successfully.')
        self.studentID_input.delete(0, tk.END)
        self.name_input.delete(0, tk.END)
        self.year_level_input.delete(0, tk.END)
        self.rfid_input.delete(0, tk.END)
        self.load_data()

    def load_data(self):
        selected_database = self.database_selector_manage.get()

        if not selected_database:
            return

        db_path = get_database_path(selected_database)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM students''')
            rows = cursor.fetchall()
            conn.close()

            self.table.delete(*self.table.get_children())  

            for row in rows:
                self.table.insert('', 'end', values=row)

        except Exception as e:
            messagebox.showerror('Database Error', str(e))

    def delete_data(self):
        selected_items = self.table.selection()
        if not selected_items:
            messagebox.showwarning('Selection Error', 'No rows selected.')
            return

        selected_database = self.database_selector_manage.get()
        db_path = resource_path(selected_database)

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for item in selected_items:
                row_id = self.table.item(item, 'values')[0]
                cursor.execute('''DELETE FROM students WHERE id = ?''', (row_id,))

            conn.commit()
            conn.close()

            messagebox.showinfo('Success', 'Selected rows deleted.')
            self.load_data()
        except Exception as e:
            messagebox.showerror('Database Error', str(e))

    def sort_by_year_level(self):
        items = self.table.get_children()
        items = [(self.table.item(item, 'values')[3], item) for item in items]
        items.sort(key=lambda x: x[0])
        for index, (_, item) in enumerate(items):
            self.table.move(item, '', index)

    def auto_insert_data(self):
        rfid = self.rfid_scanner_input.get().strip()

        if len(rfid) != 10:
            self.rfid_scanner_input.delete(0, tk.END)
            self.display_scan_status("Invalid RFID length")
            return

        db_list = self.database_selector_manage['values']

        if not db_list:
            self.rfid_scanner_input.delete(0, tk.END)
            self.display_scan_status("No event selected")
            return

        selected_event_db = self.database_selector_attendance.get()

        if selected_event_db not in db_list:
            self.rfid_scanner_input.delete(0, tk.END)
            self.display_scan_status("Invalid database selection")
            return

        if len(db_list) < 2:
            self.rfid_scanner_input.delete(0, tk.END)
            self.display_scan_status("Not enough databases for IN/OUT")
            return

        try:
            selected_index = db_list.index(selected_event_db)
            if selected_index + 1 < len(db_list):
                database_in = db_list[selected_index]
                database_out = db_list[selected_index + 1]
            else:
                database_in = db_list[selected_index]
                database_out = db_list[0]

            db_path_in = resource_path(database_in)
            db_path_out = resource_path(database_out)

            conn_read = sqlite3.connect(resource_path("SCA.db"))
            cursor_read = conn_read.cursor()
            cursor_read.execute('''SELECT * FROM students WHERE rfid = ?''', (rfid,))
            student_data = cursor_read.fetchone()
            conn_read.close()

            if not student_data:
                self.rfid_scanner_input.delete(0, tk.END)
                self.display_scan_status("Not Registered")
                return

            status_in = status_out = False

            conn_check = sqlite3.connect(db_path_in)
            cursor_check = conn_check.cursor()
            cursor_check.execute('''SELECT * FROM students WHERE rfid = ?''', (rfid,))
            existing_rfid_in = cursor_check.fetchone()
            conn_check.close()
            status_in = existing_rfid_in is not None

            conn_check = sqlite3.connect(db_path_out)
            cursor_check = conn_check.cursor()
            cursor_check.execute('''SELECT * FROM students WHERE rfid = ?''', (rfid,))
            existing_rfid_out = cursor_check.fetchone()
            conn_check.close()
            status_out = existing_rfid_out is not None

            if status_in and status_out:
                self.display_scan_status("Attendance Checked")
            elif not status_in:
                conn_write = sqlite3.connect(db_path_in)
                cursor_write = conn_write.cursor()
                cursor_write.execute('''INSERT INTO students (studentID, name, year_level, rfid) VALUES (?, ?, ?, ?)''', student_data[1:5])
                conn_write.commit()
                conn_write.close()
                self.display_scan_status("Timed In Successfully")
            elif not status_out:
                conn_write = sqlite3.connect(db_path_out)
                cursor_write = conn_write.cursor()
                cursor_write.execute('''INSERT INTO students (studentID, name, year_level, rfid) VALUES (?, ?, ?, ?)''', student_data[1:5])
                conn_write.commit()
                conn_write.close()
                self.display_scan_status("Timed Out Successfully")
            else:
                self.display_scan_status("Attendance Checked")

            self.rfid_scanner_input.delete(0, tk.END)
            self.update_table()

        except Exception as e:
            messagebox.showerror('Database Error', str(e))
            self.display_scan_status("Database Error")

    def get_in_out_databases(self, db_list, selected_index):
        if selected_index + 1 < len(db_list):
            return db_list[selected_index], db_list[selected_index + 1]
        else:
            return db_list[selected_index], db_list[0]

    def process_rfid(self, rfid, database_in, database_out):
        try:
            conn_read = sqlite3.connect(resource_path("SCA.db"))
            cursor_read = conn_read.cursor()
            cursor_read.execute('''SELECT * FROM students WHERE rfid = ?''', (rfid,))
            student_data = cursor_read.fetchone()
            conn_read.close()

            if not student_data:
                self.display_scan_status("N/A")
                return

            status_in = self.check_rfid_status(rfid, database_in)
            status_out = self.check_rfid_status(rfid, database_out)

            self.update_status(rfid, status_in, status_out, database_in, database_out)
        except sqlite3.Error as e:
            messagebox.showerror('Database Error', str(e))
            self.display_scan_status("Database Error")

    def export_data_to_file(self):
        selected_database = self.database_selector_manage.get()
        if not selected_database:
            messagebox.showwarning('Export Error', 'No database selected.')
            return

        file_name = f"{os.path.splitext(selected_database)[0]}_Data.csv"

        try:
            # Get the current sorted order of items
            items = self.table.get_children()
            sorted_items = [(self.table.item(item, 'values')[3], item) for item in items]  # Assuming sorting is by 'Year Level'
            sorted_items.sort(key=lambda x: x[0])
            
            # Extract the sorted rows
            sorted_rows = [self.table.item(item, 'values') for _, item in sorted_items]

            if not sorted_rows:
                messagebox.showinfo('Export Info', 'No data to export.')
                return

            with open(file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['ID', 'Student ID#', 'Name', 'Year Level', 'RFID'])
                writer.writerows(sorted_rows)

            messagebox.showinfo('Success', f'Data exported successfully to {file_name}.')
        except Exception as e:
            messagebox.showerror('Export Error', str(e))

    def create_new_database(self, db_name):
        if not db_name.endswith('.db'):
            messagebox.showwarning('Invalid File Name', 'Database name must end with ".db".')
            return

        db_path = get_database_path(db_name)
        if os.path.exists(db_path):
            messagebox.showwarning('File Exists', f'Database {db_name} already exists.')
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                studentID TEXT NOT NULL,
                name TEXT NOT NULL,
                year_level TEXT NOT NULL,
                rfid TEXT NOT NULL
            )
            ''')
            conn.commit()
            conn.close()

            messagebox.showinfo('Success', f'Database {db_name} created successfully.')
            self.refresh_database_list()
            
        except Exception as e:
            messagebox.showerror('Database Error', str(e))

    def create_db_button_clicked(self):
        db_name = self.new_db_name_entry.get().strip()
        if db_name:
            self.create_new_database(db_name)
        else:
            messagebox.showwarning('Input Error', 'Please enter a database name.')

    def get_sorted_database_list(self):
        db_files = [f for f in os.listdir(os.getcwd()) if f.endswith('.db')]
        db_files.sort(key=lambda x: os.path.getctime(os.path.join(os.getcwd(), x)))
        return db_files

    def refresh_database_list(self):
        db_files = self.get_sorted_database_list()

        self.database_selector_manage['values'] = db_files
        self.database_selector_attendance['values'] = db_files

        if db_files:
            selected_event_db = self.database_selector_attendance.get()
            if selected_event_db in db_files:
                self.database_selector_manage.set(selected_event_db)
                self.database_selector_attendance.set(selected_event_db)
            else:
                self.database_selector_manage.set(db_files[0])
                self.database_selector_attendance.set(db_files[0])

    def delete_database_button_clicked(self):
        selected_db = self.database_selector_manage.get()
        
        if not selected_db:
            messagebox.showwarning('Selection Error', 'No database selected for deletion.')
            return
        
        if selected_db == resource_path("SCA.db"):
            messagebox.showwarning('Deletion Error', 'Cannot delete the default database.')
            return

        confirm = messagebox.askyesno('Confirm Deletion', f'Are you sure you want to delete the database "{selected_db}"?')
        if not confirm:
            return

        try:
            os.remove(selected_db)
            self.refresh_database_list()  
            messagebox.showinfo('Success', f'Database "{selected_db}" deleted successfully.')
        except Exception as e:
            messagebox.showerror('Deletion Error', str(e))

if __name__ == "__main__":
    app = AttendanceApp()
    app.mainloop()

    