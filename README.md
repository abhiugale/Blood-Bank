🩸 Blood Bank Management SystemProject OverviewThe Blood Bank Management System is a desktop application developed in Python using the tkinter library for the Graphical User Interface (GUI), matplotlib for real-time visualization of blood inventory, and MySQL for robust data management.This system facilitates core blood bank operations, including:Donor registration and donation tracking.Real-time inventory management for all blood groups.Patient blood request submission and fulfillment.Comprehensive viewing of donor and request records.

✨ Features:
1. Donor Management: Register new donors, automatically record their donation, and update their donation history.
2. Real-time Inventory: A graphical bar chart (using Matplotlib) displays the current stock levels for all blood groups (A+, A-, B+, B-, O+, O-, AB+, AB-).
3. Blood Request Handling: Patients can submit requests for specific blood groups and units.
4. Request Fulfillment: Logic to check inventory and fulfill pending requests, automatically reducing stock upon completion.
5. Data Persistence: Uses a MySQL database to store and retrieve all donor, patient, donation, and inventory data.
6. User-Friendly Interface: A tabbed GUI (using ttk.Notebook) provides clear separation for different functions.

🛠️ Prerequisites:
    Before running the application, you must have the following installed:
    1. Python 3.x
    2. MySQL Server: Running on your system (e.g., via XAMPP, MySQL Workbench, etc.).
    
📦 Installation and Setup:
1. Install Python Dependencies:
     Open your terminal or command prompt and run the following command to install the required Python libraries:

       pip install tkinter matplotlib mysql-connector-python
3. Configure MySQL Database:
      You need to update the database credentials in the main() function of the Python script.Locate the following section in the code and replace the placeholder values with your actual MySQL         credentials:Pythondef main():
   
        # === UPDATE THESE to match your MySQL credentials ===
            DB_HOST = 'localhost'
            DB_USER = 'root'
            DB_PASSWORD = ''        # <-- put your DB password here
            DB_NAME = 'blood_bank_db'
        # ===================================================
        # ... rest of the main function

   Note: The application is designed to automatically create the database (blood_bank_db) and all necessary tables (blood_inventory, donors, donations, patients, blood_requests) upon the first successful run.
4. Run the Application:
       Execute the Python script:

       python blood_bank_app.py
