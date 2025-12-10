import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mysql.connector
from mysql.connector import Error
import datetime

class BloodBankDB:
    def __init__(self, host='localhost', user='root', password='Urvi@7860', database='blood_bank_db'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.connect()
        # Only create tables if connection is established
        if self.connection and self.connection.is_connected():
            self.create_tables()

    def connect(self):
        """
        Attempt to connect to the configured database. If the database does not exist,
        try to create it and reconnect.
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password="Urvi@7860",
                database=self.database
            )
            if self.connection.is_connected():
                print(f"Connected to MySQL database '{self.database}'")
        except Error as e:
            # If the error is because the database doesn't exist, create it
            print(f"Initial connection error: {e}")
            try:
                # Try connecting without specifying a database to create it
                temp_conn = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password="Urvi@7860",
                )
                temp_cursor = temp_conn.cursor()
                create_db_sql = f"CREATE DATABASE IF NOT EXISTS `{self.database}`"
                temp_cursor.execute(create_db_sql)
                temp_conn.commit()
                temp_cursor.close()
                temp_conn.close()
                # Reconnect to the created database
                self.connection = mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password="Urvi@7860",
                    database=self.database
                )
                if self.connection.is_connected():
                    print(f"Created and connected to database '{self.database}'")
            except Error as e2:
                print(f"Error creating or connecting to database: {e2}")
                self.connection = None

    def create_tables(self):
        if not self.connection or not self.connection.is_connected():
            print("No DB connection available to create tables.")
            return

        try:
            cursor = self.connection.cursor()
            
            # Create blood_inventory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blood_inventory (
                    blood_group VARCHAR(3) PRIMARY KEY,
                    quantity INT DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Create donors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS donors (
                    donor_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    blood_group VARCHAR(3) NOT NULL,
                    age INT NOT NULL,
                    contact VARCHAR(15) NOT NULL,
                    last_donation_date DATE,
                    donation_count INT DEFAULT 0,
                    registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create donations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    donation_id INT AUTO_INCREMENT PRIMARY KEY,
                    donor_id INT,
                    blood_group VARCHAR(3) NOT NULL,
                    donation_date DATE NOT NULL,
                    FOREIGN KEY (donor_id) REFERENCES donors(donor_id),
                    FOREIGN KEY (blood_group) REFERENCES blood_inventory(blood_group)
                )
            """)
            
            # Create patients table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    patient_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    blood_group VARCHAR(3) NOT NULL,
                    age INT NOT NULL,
                    contact VARCHAR(15) NOT NULL,
                    registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create blood_requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blood_requests (
                    request_id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id INT,
                    blood_group VARCHAR(3) NOT NULL,
                    units_needed INT NOT NULL,
                    request_date DATE NOT NULL,
                    status ENUM('Pending', 'Approved', 'Rejected', 'Completed') DEFAULT 'Pending',
                    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                )
            """)
            
            # Initialize blood inventory with default values (INSERT IGNORE equivalent)
            blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
            for bg in blood_groups:
                cursor.execute("""
                    INSERT INTO blood_inventory (blood_group, quantity)
                    SELECT %s, %s FROM DUAL
                    WHERE NOT EXISTS (
                        SELECT 1 FROM blood_inventory WHERE blood_group = %s
                    )
                """, (bg, 0, bg))
            
            self.connection.commit()
            cursor.close()
        except Error as e:
            print(f"Error creating tables: {e}")

    def add_donor(self, name, blood_group, age, contact):
        """
        Add a donor, increase inventory by 1 unit, record donation and update donor's donation_count.
        Returns True on success, False on failure.
        """
        if not self.connection or not self.connection.is_connected():
            print("No DB connection.")
            return False

        try:
            cursor = self.connection.cursor()
            
            # 1) Insert donor and get donor_id immediately
            cursor.execute("""
                INSERT INTO donors (name, blood_group, age, contact)
                VALUES (%s, %s, %s, %s)
            """, (name, blood_group, age, contact))
            donor_id = cursor.lastrowid

            # 2) Update blood inventory
            cursor.execute("""
                UPDATE blood_inventory
                SET quantity = quantity + 1
                WHERE blood_group = %s
            """, (blood_group,))

            # 3) Record donation
            cursor.execute("""
                INSERT INTO donations (donor_id, blood_group, donation_date)
                VALUES (%s, %s, CURDATE())
            """, (donor_id, blood_group))

            # 4) Update donor's donation count and last donation date
            cursor.execute("""
                UPDATE donors
                SET donation_count = donation_count + 1,
                    last_donation_date = CURDATE()
                WHERE donor_id = %s
            """, (donor_id,))

            self.connection.commit()
            cursor.close()
            return True

        except Error as e:
            print(f"Error adding donor: {e}")
            try:
                if self.connection:
                    self.connection.rollback()
            except Exception:
                pass
            return False

    def get_blood_inventory(self):
        if not self.connection or not self.connection.is_connected():
            return {}
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM blood_inventory ORDER BY blood_group")
            result = cursor.fetchall()
            cursor.close()
            inventory = {row['blood_group']: row['quantity'] for row in result}
            return inventory
        except Error as e:
            print(f"Error getting inventory: {e}")
            return {}

    def get_all_donors(self):
        if not self.connection or not self.connection.is_connected():
            return []
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT d.*,
                       (SELECT COUNT(*) FROM donations WHERE donor_id = d.donor_id) as total_donations
                FROM donors d
                ORDER BY d.registered_date DESC
            """)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"Error getting donors: {e}")
            return []

    def request_blood(self, patient_name, blood_group, age, contact, units_needed):
        if not self.connection or not self.connection.is_connected():
            return False
        try:
            cursor = self.connection.cursor()
            # Check if patient exists
            cursor.execute("SELECT patient_id FROM patients WHERE name = %s AND contact = %s", 
                           (patient_name, contact))
            patient = cursor.fetchone()
            if patient:
                patient_id = patient[0]
            else:
                cursor.execute("""
                    INSERT INTO patients (name, blood_group, age, contact)
                    VALUES (%s, %s, %s, %s)
                """, (patient_name, blood_group, age, contact))
                patient_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO blood_requests (patient_id, blood_group, units_needed, request_date)
                VALUES (%s, %s, %s, CURDATE())
            """, (patient_id, blood_group, units_needed))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error requesting blood: {e}")
            try:
                if self.connection:
                    self.connection.rollback()
            except Exception:
                pass
            return False

    def fulfill_request(self, request_id):
        if not self.connection or not self.connection.is_connected():
            print("No DB connection.")
            return False
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT blood_group, units_needed, status
                FROM blood_requests
                WHERE request_id = %s
            """, (request_id,))
            req = cursor.fetchone()
            if not req:
                print("Request not found.")
                cursor.close()
                return False

            blood_group, units_needed, status = req
            if status == 'Completed':
                print("Request already completed.")
                cursor.close()
                return False

            # Check inventory safely
            cursor.execute("SELECT quantity FROM blood_inventory WHERE blood_group = %s", (blood_group,))
            qty_row = cursor.fetchone()
            if not qty_row:
                print("Blood group not found in inventory.")
                cursor.close()
                return False

            current_qty = qty_row[0]
            if current_qty >= units_needed:
                cursor.execute("""
                    UPDATE blood_inventory
                    SET quantity = quantity - %s
                    WHERE blood_group = %s
                """, (units_needed, blood_group))

                cursor.execute("""
                    UPDATE blood_requests
                    SET status = 'Completed'
                    WHERE request_id = %s
                """, (request_id,))
                self.connection.commit()
                cursor.close()
                return True
            else:
                print("Insufficient stock.")
                cursor.close()
                return False
        except Error as e:
            print(f"Error fulfilling request: {e}")
            try:
                if self.connection:
                    self.connection.rollback()
            except Exception:
                pass
            return False

    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")


class BloodBankApp:
    def __init__(self, root, db: BloodBankDB):
        self.root = root
        self.db = db
        self.root.title("Blood Bank Management System")
        self.root.geometry("1000x800")
        self.root.configure(bg='#F0F0F0')

        # Setup UI
        self.setup_ui()

        # Load initial data
        self.update_chart()

    def setup_ui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tab 1: Donor Management
        self.donor_tab = tk.Frame(self.notebook, bg='#F0F0F0')
        self.notebook.add(self.donor_tab, text='Donor Management')
        self.setup_donor_tab()

        # Tab 2: Blood Inventory
        self.inventory_tab = tk.Frame(self.notebook, bg='#F0F0F0')
        self.notebook.add(self.inventory_tab, text='Blood Inventory')
        self.setup_inventory_tab()

        # Tab 3: Blood Requests
        self.request_tab = tk.Frame(self.notebook, bg='#F0F0F0')
        self.notebook.add(self.request_tab, text='Blood Requests')
        self.setup_request_tab()

        # Tab 4: View Donors
        self.view_tab = tk.Frame(self.notebook, bg='#F0F0F0')
        self.notebook.add(self.view_tab, text='View All Donors')
        self.setup_view_tab()

    def setup_donor_tab(self):
        frame = tk.Frame(self.donor_tab, bg='#F0F0F0')
        frame.pack(pady=20)

        tk.Label(frame, text="Name:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.name_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="Blood Group:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=1, column=0, padx=10, pady=10, sticky='e')
        self.blood_group_combobox = ttk.Combobox(frame, values=['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'],
                                                 font=("Arial", 12), width=27)
        self.blood_group_combobox.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(frame, text="Age:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=2, column=0, padx=10, pady=10, sticky='e')
        self.age_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.age_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(frame, text="Contact:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=3, column=0, padx=10, pady=10, sticky='e')
        self.contact_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.contact_entry.grid(row=3, column=1, padx=10, pady=10)

        btn_frame = tk.Frame(frame, bg='#F0F0F0')
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        tk.Button(btn_frame, text="Add Donor", command=self.add_donor,
                  font=("Arial", 12, "bold"), bg='#66CC66', fg='white', width=15).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Clear Fields", command=self.clear_fields,
                  font=("Arial", 12, "bold"), bg='#FF9966', fg='white', width=15).pack(side='left', padx=10)

    def setup_inventory_tab(self):
        chart_frame = tk.Frame(self.inventory_tab, bg='white')
        chart_frame.pack(fill='both', expand=True, padx=20, pady=20)

        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        tk.Button(self.inventory_tab, text="Refresh Chart", command=self.update_chart,
                  font=("Arial", 12, "bold"), bg='#6699CC', fg='white').pack(pady=10)

    def setup_request_tab(self):
        frame = tk.Frame(self.request_tab, bg='#F0F0F0')
        frame.pack(pady=20)

        tk.Label(frame, text="Patient Name:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.patient_name_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.patient_name_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(frame, text="Blood Group Needed:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=1, column=0, padx=10, pady=10, sticky='e')
        self.request_blood_group = ttk.Combobox(frame, values=['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-'],
                                                font=("Arial", 12), width=27)
        self.request_blood_group.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(frame, text="Patient Age:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=2, column=0, padx=10, pady=10, sticky='e')
        self.patient_age_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.patient_age_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(frame, text="Contact:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=3, column=0, padx=10, pady=10, sticky='e')
        self.patient_contact_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.patient_contact_entry.grid(row=3, column=1, padx=10, pady=10)

        tk.Label(frame, text="Units Needed:", font=("Arial", 12, "bold"), bg='#F0F0F0').grid(row=4, column=0, padx=10, pady=10, sticky='e')
        self.units_needed_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.units_needed_entry.grid(row=4, column=1, padx=10, pady=10)

        tk.Button(frame, text="Submit Blood Request", command=self.submit_blood_request,
                  font=("Arial", 12, "bold"), bg='#FF6666', fg='white', width=20).grid(row=5, column=0, columnspan=2, pady=20)

        self.setup_requests_list()

    def setup_requests_list(self):
        tree_frame = tk.Frame(self.request_tab)
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        self.requests_tree = ttk.Treeview(tree_frame, columns=("ID", "Patient", "Blood Group", "Units", "Date", "Status"),
                                          show="headings", yscrollcommand=scrollbar.set)

        self.requests_tree.heading("ID", text="Request ID")
        self.requests_tree.heading("Patient", text="Patient Name")
        self.requests_tree.heading("Blood Group", text="Blood Group")
        self.requests_tree.heading("Units", text="Units Needed")
        self.requests_tree.heading("Date", text="Request Date")
        self.requests_tree.heading("Status", text="Status")

        self.requests_tree.column("ID", width=80)
        self.requests_tree.column("Patient", width=150)
        self.requests_tree.column("Blood Group", width=100)
        self.requests_tree.column("Units", width=100)
        self.requests_tree.column("Date", width=100)
        self.requests_tree.column("Status", width=100)

        self.requests_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.requests_tree.yview)

        tk.Button(self.request_tab, text="Fulfill Selected Request", command=self.fulfill_selected_request,
                  font=("Arial", 12, "bold"), bg='#66CC66', fg='white').pack(pady=10)

        tk.Button(self.request_tab, text="Refresh Requests", command=self.load_pending_requests,
                  font=("Arial", 12, "bold"), bg='#6699CC', fg='white').pack(pady=5)

        self.load_pending_requests()

    def setup_view_tab(self):
        tree_frame = tk.Frame(self.view_tab)
        tree_frame.pack(fill='both', expand=True, padx=20, pady=20)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')

        self.donors_tree = ttk.Treeview(tree_frame, columns=("ID", "Name", "Blood Group", "Age", "Contact", "Donations", "Last Donation"),
                                        show="headings", yscrollcommand=scrollbar.set)

        self.donors_tree.heading("ID", text="Donor ID")
        self.donors_tree.heading("Name", text="Name")
        self.donors_tree.heading("Blood Group", text="Blood Group")
        self.donors_tree.heading("Age", text="Age")
        self.donors_tree.heading("Contact", text="Contact")
        self.donors_tree.heading("Donations", text="Total Donations")
        self.donors_tree.heading("Last Donation", text="Last Donation")

        self.donors_tree.column("ID", width=80)
        self.donors_tree.column("Name", width=150)
        self.donors_tree.column("Blood Group", width=100)
        self.donors_tree.column("Age", width=80)
        self.donors_tree.column("Contact", width=150)
        self.donors_tree.column("Donations", width=120)
        self.donors_tree.column("Last Donation", width=120)

        self.donors_tree.pack(fill='both', expand=True)
        scrollbar.config(command=self.donors_tree.yview)

        tk.Button(self.view_tab, text="Refresh Donor List", command=self.load_donors,
                  font=("Arial", 12, "bold"), bg='#6699CC', fg='white').pack(pady=10)

        self.load_donors()

    def add_donor(self):
        name = self.name_entry.get().strip()
        blood_group = self.blood_group_combobox.get().strip()
        age = self.age_entry.get().strip()
        contact = self.contact_entry.get().strip()

        if not all([name, blood_group, age, contact]):
            messagebox.showerror("Input Error", "Please fill all fields!")
            return

        if not age.isdigit() or int(age) < 18 or int(age) > 65:
            messagebox.showerror("Input Error", "Age must be between 18 and 65!")
            return

        if self.db.add_donor(name, blood_group, int(age), contact):
            messagebox.showinfo("Success", "Donor added successfully!")
            self.clear_fields()
            self.update_chart()
            self.load_donors()
        else:
            messagebox.showerror("Error", "Failed to add donor!")

    def clear_fields(self):
        self.name_entry.delete(0, tk.END)
        self.blood_group_combobox.set('')
        self.age_entry.delete(0, tk.END)
        self.contact_entry.delete(0, tk.END)

    def update_chart(self):
        blood_data = self.db.get_blood_inventory()
        if not blood_data:
            # Nothing to show
            self.ax.clear()
            self.ax.set_title("Blood Group Availability")
            self.canvas.draw()
            return

        blood_groups = list(blood_data.keys())
        quantities = list(blood_data.values())

        self.ax.clear()
        # default matplotlib colors (don't force colors) — but you can set custom colors if you want
        bars = self.ax.bar(blood_groups, quantities)
        self.ax.set_title("Blood Group Availability", fontsize=14, fontweight='bold')
        self.ax.set_xlabel("Blood Groups", fontsize=12, fontweight='bold')
        self.ax.set_ylabel("Units Available", fontsize=12, fontweight='bold')
        self.ax.tick_params(axis='x', labelsize=10)
        self.ax.tick_params(axis='y', labelsize=10)

        # Add value labels above bars
        for bar, qty in zip(bars, quantities):
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width() / 2, height + 0.1, str(qty),
                         ha='center', va='bottom', fontsize=10, color='black', fontweight='bold')

        self.canvas.draw()

    def submit_blood_request(self):
        name = self.patient_name_entry.get().strip()
        blood_group = self.request_blood_group.get().strip()
        age = self.patient_age_entry.get().strip()
        contact = self.patient_contact_entry.get().strip()
        units = self.units_needed_entry.get().strip()

        if not all([name, blood_group, age, contact, units]):
            messagebox.showerror("Input Error", "Please fill all fields!")
            return

        if not units.isdigit() or int(units) <= 0:
            messagebox.showerror("Input Error", "Units needed must be a positive number!")
            return

        if not age.isdigit():
            messagebox.showerror("Input Error", "Age must be a number!")
            return

        if self.db.request_blood(name, blood_group, int(age), contact, int(units)):
            messagebox.showinfo("Success", "Blood request submitted successfully!")
            # Clear fields
            self.patient_name_entry.delete(0, tk.END)
            self.request_blood_group.set('')
            self.patient_age_entry.delete(0, tk.END)
            self.patient_contact_entry.delete(0, tk.END)
            self.units_needed_entry.delete(0, tk.END)

            # Refresh requests list and chart
            self.load_pending_requests()
            self.update_chart()
        else:
            messagebox.showerror("Error", "Failed to submit blood request!")

    def load_pending_requests(self):
        if not self.db.connection:
            return
        try:
            # Clear existing items
            for item in self.requests_tree.get_children():
                self.requests_tree.delete(item)

            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT r.request_id, p.name, r.blood_group, r.units_needed,
                       r.request_date, r.status
                FROM blood_requests r
                JOIN patients p ON r.patient_id = p.patient_id
                WHERE r.status != 'Completed'
                ORDER BY r.request_date DESC
            """)
            requests = cursor.fetchall()
            cursor.close()

            for req in requests:
                self.requests_tree.insert("", tk.END, values=(
                    req['request_id'],
                    req['name'],
                    req['blood_group'],
                    req['units_needed'],
                    req['request_date'],
                    req['status']
                ))
        except Error as e:
            print(f"Error loading requests: {e}")

    def fulfill_selected_request(self):
        selection = self.requests_tree.selection()
        if not selection:
            messagebox.showerror("Selection Error", "Please select a request to fulfill!")
            return

        item = self.requests_tree.item(selection[0])
        request_id = item['values'][0]

        if self.db.fulfill_request(request_id):
            messagebox.showinfo("Success", "Blood request fulfilled successfully!")
            self.load_pending_requests()
            self.update_chart()
        else:
            messagebox.showerror("Error", "Failed to fulfill request! Check blood inventory or request status.")

    def load_donors(self):
        if not self.db.connection:
            return
        try:
            for item in self.donors_tree.get_children():
                self.donors_tree.delete(item)

            donors = self.db.get_all_donors()
            for donor in donors:
                last_donation = donor['last_donation_date'].strftime("%Y-%m-%d") if donor['last_donation_date'] else "Never"
                self.donors_tree.insert("", tk.END, values=(
                    donor['donor_id'],
                    donor['name'],
                    donor['blood_group'],
                    donor['age'],
                    donor['contact'],
                    donor.get('total_donations', 0),
                    last_donation
                ))
        except Error as e:
            print(f"Error loading donors: {e}")

    def on_closing(self):
        if self.db:
            self.db.close()
        self.root.destroy()

def main():
    # === UPDATE THESE to match your MySQL credentials ===
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''        # <-- put your DB password here (do NOT hardcode in production)
    DB_NAME = 'blood_bank_db'
    # ===================================================

    root = tk.Tk()
    db = BloodBankDB(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    app = BloodBankApp(root, db)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
