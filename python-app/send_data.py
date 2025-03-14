import psycopg2
import pandas as pd
import random
import time
import os

# Log file path - Ensure this directory exists or it will fail to write
log_file_path = '/app/insertion_log.txt'

# Database connection details
host = "redshift"  # This assumes your Redshift container is named 'redshift'
database = "devdb"
user = "awsuser"
password = "redshiftpassword"
port = "5439"

# Establish connection to Redshift
def connect_to_db():
    try:
        conn = psycopg2.connect(
            dbname=database, user=user, password=password, host=host, port=port
        )
        return conn
    except Exception as e:
        log_output(f"Error connecting to the database: {e}")
        raise

conn = connect_to_db()
cursor = conn.cursor()

# Create the table (if it doesn't exist)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_data (
        transaction_id INT IDENTITY(1,1) PRIMARY KEY,
        customer_id INT,
        amount DECIMAL(10, 2),
        transaction_date TIMESTAMP
    );
""")
conn.commit()

# Function to log output to a file in the mounted volume
def log_output(message):
    try:
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{time.ctime()}: {message}\n")
    except Exception as e:
        print(f"Error writing to log file: {e}")

# Generate large data to simulate a data stream
def generate_data(num_rows=1000):
    for _ in range(num_rows):
        customer_id = random.randint(1000, 9999)
        amount = round(random.uniform(10.0, 500.0), 2)
        transaction_date = pd.to_datetime('today') - pd.to_timedelta(random.randint(0, 100), unit='D')
        yield (customer_id, amount, transaction_date)

# Insert large data into the table
def insert_data(batch_size=100):
    try:
        # Insert data in batches
        for batch in generate_data(batch_size):
            cursor.execute(
                "INSERT INTO sales_data (customer_id, amount, transaction_date) VALUES (%s, %s, %s)",
                batch
            )
        conn.commit()
    except Exception as e:
        log_output(f"Error inserting data: {e}")
        print(f"Error inserting data: {e}")
        conn.rollback()

# Simulate sending data in batches
if __name__ == "__main__":
    try:
        total_rows = 50000  # Total number of rows to insert
        batch_size = 100    # Number of rows per batch
        num_batches = total_rows // batch_size

        for batch_num in range(num_batches):
            insert_data(batch_size)  # Insert 100 rows at a time
            log_output(f"Inserted {batch_size * (batch_num + 1)} rows of data.")  # Log the insertion
            print(f"Inserted {batch_size * (batch_num + 1)} rows of data.")
            time.sleep(1)  # Optional: Pause for a second between batches

        log_output(f"Successfully inserted {total_rows} rows of data.")  # Log the completion
        print(f"Successfully inserted {total_rows} rows of data.")
    except KeyboardInterrupt:
        log_output("Data insertion stopped.")
        print("Data insertion stopped.")
    except Exception as e:
        log_output(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
    finally:
        cursor.close()
        conn.close()
        log_output("Database connection closed.")