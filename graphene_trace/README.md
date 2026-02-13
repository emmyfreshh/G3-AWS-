## Authentication
- Login/Logout for patients, clinicians, and admins
- Password reset for patients, clinicians.

### Patient Features
- Real-time pressure heat map on dashboard with explanations
- Pressure data graphs over time using Chart.js
- Notifications for high pressure with guidance
- Comments linked to specific data points
- Receive feedback from clinicians

### Clinician Features
- List of patients with alert filtering
- View patient pressure history graphs
- Flagged high-pressure periods in red
- Read and reply to patient comments

### Admin Features
- Create clinician and patient accounts
- View all users
- Delete user accounts
- Reset user passwords
- Assign patients to clinicians
- Upload CSV files with pressure data for specific dates for specific users(patients). i want the web app to do all these.

## Setup

1. Install dependencies:
   ```
   pip install django
   ```

2. Run migrations:
   ```
   python manage.py migrate
   ```

3. Create superuser:
   ```
   python manage.py createsuperuser
   ```

4. Run the server:
   ```
   python manage.py runserver
   ```

5. Access at http://127.0.0.1:8000/

## Usage

- Register as a patient or clinician at `http://127.0.0.1:8000/accounts/register/` by selecting your role.
- Admins are created by existing admins through the admin dashboard.
- Login to access role-specific dashboard
- Patients can view data and add comments
- Clinicians can manage patients and provide feedback
- Admins can create users and upload pressure data via CSV

## CSV Upload Format

For uploading pressure data to a specific patient account, select the patient from the dropdown, choose the date, and upload the CSV file. The CSV file should have the following columns:
- sensor_location: Location of the sensor (e.g., left_hip)
- pressure_value: Pressure value (numeric)

Specify the date for the data in the upload form.

## Models

- User (custom with role)
- PressureData
- Comment
- Notification

## Future Enhancements

- Real-time data updates
- Advanced visualizations with Chart.js/D3.js
- API endpoints for mobile apps
- Email notifications