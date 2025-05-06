# TechConf 2025 Registration App

A FastAPI-based web application for managing registrations for a technology conference.

## Features

- User registration and authentication
- Profile management
- List of registered users
- Modern Bootstrap 5 UI

## Requirements

- Python 3.8+
- pip

## Setup Instructions

1. **Clone the repository**
   ```sh
   git clone https://github.com/Drakenbolt/techconf-practice-proj.git
   cd YOUR-REPO-NAME
   ```

2. **Create and activate a virtual environment**
   ```sh
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the project root with the following content:
   ```
   SECRET_KEY=your-secret-key-here
   ```

5. **Run the application**
   ```sh
   uvicorn app.main:app --reload
   ```

6. **Open in your browser**

   Visit [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Project Structure

```
.
├── app/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── templates/
│   └── static/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## License

MIT License 