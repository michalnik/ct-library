# CT Library

## Installation

1. Install dependencies using pip:
```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## Database Setup

2. Run database migrations:
```bash
python manage.py migrate
```

## Load Test Data

3. Load presentation data:
Please, be aware of the count. The count greater than 10 leads to a long loading time.
```bash
python manage.py prezentation_data
```

Optional parameters:
- `--count` - Number of records per model (default: 10)
- `--password` - Password for generated users (default: 'asd')

Example with custom values:
```bash
python manage.py prezentation_data --count 20 --password mypassword
```

## Running Tests

4. Run tests:
```bash
pytest
```
I have a few words about the tests… The tests use random data, so occasionally they fail :-(. It would definitely be better to use fixed fixtures. I used random data because for most of my testing it was sufficient, and I had previously written a script to generate test data before I started writing my own tests.


5. Run development server
```bash
python manage.py runserver
```

6. Use REST API 
Open `http://localhost:8000/api/v1/docs` in your browser and play with the API.

## Application Description
- The application uses **basedpyright** for type checking; however, for convenience, some checks in the configuration have been relaxed, and inline `ignore` comments are occasionally used.  

- Tests currently cover only the most essential parts of borrowing and returning items. They need to be expanded significantly before the application can be considered bug-free.  

- **SQLite** was chosen for rapid prototyping. It seems somewhat slow for generating test data, but **PostgreSQL** has not been tested. Otherwise, the database has met the requirements.  

- Many routine tasks in **django-ninja** can be implemented in multiple ways, and some features are less well documented. Overall, **django-ninja** is considered more developer-friendly than **Django REST Framework**.
