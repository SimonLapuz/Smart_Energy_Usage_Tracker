# ⚡ Smart Energy Usage Tracker

Final project for **CPE009A**

---

## 📌 Overview

The **Smart Energy Usage Tracker** is a web-based application designed to help users monitor and analyze their daily electricity and water consumption. It provides an intuitive interface for logging usage, visualizing trends, and estimating utility bills.

This project demonstrates full-stack development using a Python backend and a modern JavaScript frontend.

---

## 🚀 Features

- 📊 **Dashboard**
  - View average daily electricity and water usage
  - See estimated monthly bill
  - Visualize recent 7-day consumption with charts

- 📝 **Usage Logging**
  - Add electricity and water usage entries
  - Include optional notes
  - Delete entries easily

- 📈 **Trends Analysis**
  - Weekly and monthly consumption charts
  - Separate visualization for electricity and water

- 💸 **Bill Estimator**
  - Calculate estimated bill based on usage
  - Customizable electricity and water rates
  - Includes fixed charges

---

## 🛠️ Tech Stack

### Frontend
- HTML, CSS, JavaScript
- Chart.js (for data visualization)

### Backend
- Python
- Flask (REST API)
- Flask-CORS

### Database
- SQLite

---

## 📂 Project Structure
Smart_Energy_Usage_Tracker/
│
├── app.py
├── database.py
├── energy.db
│
└── templates/
        └── index.html


---

## ⚙️ Installation & Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/Smart_Energy_Usage_Tracker.git
cd Smart_Energy_Usage_Tracker

2. Install dependencies:
pip install flask flask-cors

3. Run the application:
python app.py

4. Open in browser:
http://localhost:5000


🧪 Optional: Seed Sample Data
To populate the database with sample entries:
python database.py


📡 API Endpoints
Method	    Endpoint	        Description
GET	        /api/entries	    Get all entries
POST	    /api/entries	    Add a new entry
DELETE	    /api/entries/<id>	Delete an entry
GET	        /api/dashboard	    Dashboard summary
GET	        /api/trends	        Usage trends
GET	        /api/bill	        Estimate utility bill


📚 Learnings
Built a full-stack web application using Flask and JavaScript
Implemented RESTful API design
Worked with SQLite for data persistence
Integrated dynamic charts using Chart.js
Practiced UI/UX design principles


👨‍💻 Author
Simon Parick P. Lapuz
Huone Formilleza
Vryant Heindriech Kyle A. Sy
Jacob V. Salamanca
Romar V. Lemmer
Jared Patrick Mapaye


📄 License
This project is for academic purposes under CPE009A.

