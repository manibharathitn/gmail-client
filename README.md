# Gmail Client

## Description

This project syncs the emails from Gmail using Google API and processes the emails based on a rule engine.

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL

### Steps

1. Clone the repository:
```bash
git clone https://github.com/manibharathitn/gmail-client.git
```

2. Navigate to the project directory:
```bash
cd gmail-client
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up the PostgreSQL database:
In your local setup postgresql should be installed and running. Create a database and a user with the following commands:
```sql
CREATE DATABASE emaildb;
```

5. Set up the environment variables:
Create a .env file in the project root directory and add your database connection string:
```bash
DATABASE_URL=postgresql://user:password@localhost/emaildb
```

6. Run the migrations:
```bash
alembic upgrade head
```

6. Run the driver script:
```bash
python driver.py
```

