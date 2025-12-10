🩸 Blood Bank Management SystemProject OverviewThe Blood Bank Management System is a desktop application developed in Python using the tkinter library for the Graphical User Interface (GUI), matplotlib for real-time visualization of blood inventory, and MySQL for robust data management.This system facilitates core blood bank operations, including:Donor registration and donation tracking.Real-time inventory management for all blood groups.Patient blood request submission and fulfillment.Comprehensive viewing of donor and request records.

✨ Features
1. Donor Management: Register new donors, automatically record their donation, and update their donation history.
2. Real-time Inventory: A graphical bar chart (using Matplotlib) displays the current stock levels for all blood groups (A+, A-, B+, B-, O+, O-, AB+, AB-).
3. Blood Request Handling: Patients can submit requests for specific blood groups and units.
4. Request Fulfillment: Logic to check inventory and fulfill pending requests, automatically reducing stock upon completion.
5. Data Persistence: Uses a MySQL database to store and retrieve all donor, patient, donation, and inventory data.
6. User-Friendly Interface: A tabbed GUI (using ttk.Notebook) provides clear separation for different functions.

🛠️ Prerequisites
    Before running the application, you must have the following installed:
    1. Python 3.x
    2. MySQL Server: Running on your system (e.g., via XAMPP, MySQL Workbench, etc.).
    
📦 Installation and Setup
1. Install Python Dependencies
     Open your terminal or command prompt and run the following command to install the required Python libraries:
       Bash: pip install tkinter matplotlib mysql-connector-python
2. Configure MySQL Database
      You need to update the database credentials in the main() function of the Python script.Locate the following section in the code and replace the placeholder values with your actual MySQL         credentials:Pythondef main():
        # === UPDATE THESE to match your MySQL credentials ===
            DB_HOST = 'localhost'
            DB_USER = 'root'
            DB_PASSWORD = ''        # <-- put your DB password here
            DB_NAME = 'blood_bank_db'
        # ===================================================
        # ... rest of the main function

   Note: The application is designed to automatically create the database (blood_bank_db) and all necessary tables (blood_inventory, donors, donations, patients, blood_requests) upon the first successful run.
3. Run the Application
       Execute the Python script:
               Bash: python blood_bank_app.py

🖥️ Application Usage
    The application opens with a four-tab interface:
    1. Donor ManagementEnter the Name, Blood Group, Age (must be between 18 and 65 for a donation), and Contact of the donor.Click Add Donor. This action registers the donor, records a donation,        increments their donation count, and updates the main Blood Inventory.
    2. Blood InventoryThis tab displays the current Units Available for all eight standard blood groups in a dynamic bar chart.Click Refresh Chart to update the visualization with the latest            data.
    3. Blood RequestsSubmit a Request: Enter Patient Name, Blood Group Needed, Patient Age, Contact, and Units Needed. Click Submit Blood Request.Fulfill Requests: The lower half of the tab             lists all uncompleted requests.Select a request from the list.Click Fulfill Selected Request. The system will check the inventory. If stock is sufficient, the request status is set to            'Completed', and the inventory is reduced. An error message appears if stock is insufficient.
    4. View All DonorsDisplays a comprehensive list of all registered donors, including their total Donation Count and the Last Donation date.Click Refresh Donor List to load the most current           data.
