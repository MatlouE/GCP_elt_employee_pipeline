import os
import random
import string
from datetime import datetime
from dotenv import load_dotenv  # Fixed import
from faker import Faker
from google.cloud import storage
import pandas as pd

# Load environment variables from .env file
load_dotenv()  # Fixed function call

# Specify number of employees
num_employees = 100

# GCS configuration
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID') or os.getenv('GOOGLE_CLOUD_PROJECT') or 'emp-pipelineprj'
CSV_FILE_NAME = 'employees4.csv'

# Create a Faker instance
fake = Faker()

# List of employee objects
employees = []

# Move this outside the loop to avoid recreating it 100 times
department_jobs = {
    'HR': ['HR Manager', 'Recruiter', 'Talent Acquisition Specialist', 'HR Coordinator'],
    'Finance': ['Financial Analyst', 'Accountant', 'Controller', 'Payroll Specialist'],
    'IT': ['Software Engineer', 'Systems Administrator', 'Data Analyst', 'DevOps Engineer'],
    'Sales': ['Sales Representative', 'Account Executive', 'Sales Manager', 'Business Development Rep'],
    'Marketing': ['Marketing Specialist', 'Content Strategist', 'Brand Manager', 'SEO Specialist']
}

for _ in range(num_employees):
    # Generate random employee data
    first_name = fake.first_name()
    last_name = fake.last_name()
    email = f"{first_name.lower()}.{last_name.lower()}@email.com"
    phone_number = fake.phone_number()
    
    # Replace newlines in fake addresses with commas for clean CSV rows
    address = fake.address().replace('\n', ' ').replace(',', ';')
    
    department = random.choice(list(department_jobs.keys()))
    job_title = random.choice(department_jobs[department])
    salary = round(random.uniform(40000, 120000), 2)
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    # Create employee object
    employee = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone_number": phone_number,
        "address": address,
        "job_title": job_title,
        "department": department,
        "salary": salary,
        "password": password
    }
    
    employees.append(employee)

# Create a DataFrame from the employee data
df = pd.DataFrame(employees)

# Save to CSV
df.to_csv(CSV_FILE_NAME, index=False)
print(f"Data saved to {CSV_FILE_NAME}")

# Also save a timestamped local copy for safekeeping
backup_dir = "local_exports"
os.makedirs(backup_dir, exist_ok=True)
ts = datetime.now().strftime("%Y%m%dT%H%M%SZ")
local_backup_name = f"{os.path.splitext(CSV_FILE_NAME)[0]}_{ts}.csv"
local_backup_path = os.path.join(backup_dir, local_backup_name)
df.to_csv(local_backup_path, index=False)
print(f"Local backup saved to {local_backup_path}")

# Upload to GCS
def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Upload a file to the GCS bucket"""
    if not bucket_name:
        print("Set GCS_BUCKET_NAME environment variable to upload to GCS")
        return False

    try:
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)
        print(f"File {source_file_name} uploaded to gs://{bucket_name}/{destination_blob_name}")
        return True
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return False

# Upload CSV to GCS
if GCS_BUCKET_NAME:
    upload_to_gcs(GCS_BUCKET_NAME, CSV_FILE_NAME, CSV_FILE_NAME)
else:
    print("Set GCS_BUCKET_NAME environment variable to upload to GCS")

print(f"\nGenerated {len(employees)} employee records")