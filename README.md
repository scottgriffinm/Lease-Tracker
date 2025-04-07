# Property Management Dashboard Demo

A Django-based rental property management system with an interactive dashboard. It handles properties, units, tenants, leases, payments, and rental applications using Bootstrap, Chart.js, and DataTables. Currently live at https://scottgriffinm.pythonanywhere.com.

**Project Structure:**

- **manage.py:** Command-line utility to run Django tasks.
- **property_management/**  
  - *settings.py:* Contains project settings (database, installed apps, middleware, etc.).
  - *urls.py:* Routes requests to the appropriate app.
  - *wsgi.py/asgi.py:* Deployment configurations.
- **rentals/** (Main App)  
  - *models.py:* Defines models: Property, Unit, Tenant, Lease, Payment, Charge, and Application.
  - *views.py:* Contains the dashboard view that aggregates data for display.
  - *urls.py:* Maps URL patterns (e.g., root URL to dashboard).
  - *admin.py:* Placeholder for admin customizations.
  - *tests.py:* For writing tests.
  - *migrations/*: Database migration files.
  - *management/commands/seed_data.py:* Seeds the database with fake data using Faker.
  - *templates/rentals/dashboard.html:* HTML template for the dashboard with embedded CSS/JS.

**Installation & Setup:**

1. Clone the repository.
2. Create a virtual environment and install dependencies (ensure Django 5.1.7 and Faker are included).
3. Run migrations:
```
python manage.py migrate
```
4. Seed the database with:
```
python manage.py seed_data
```
5. Start the development server:
```
python manage.py runserver
```
6. Open your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

**Usage:**  
The dashboard displays outstanding balances, unit statuses (occupied, vacant, pending), expiring leases, tasks, and recent activity. Use table headers to sort data and filter rental applications by status.

**Future Enhancements:**  
- Enhanced Django admin customization  
- User authentication and tenant portal  
- REST API and advanced reporting

**License:**  
MIT License


<img width="1469" alt="Screenshot 2025-04-01 at 1 26 09 PM" src="https://github.com/user-attachments/assets/fea69ff7-6234-4f60-ab30-26e66dd23e23" />

