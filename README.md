

### 🧠 Django Country Population API

API to get countries and their population
---

### Installation

Use the package manager pip to install **virtualenv** (if you don’t already have it):

```bash
pip install virtualenv
```

Create a new Python environment:

```bash
virtualenv venv
```

Activate your environment:

```bash
source venv/bin/activate     # For Mac/Linux
venv\Scripts\activate        # For Windows users
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### Environment Variables

Create a `.env` file in the project root and add your details:

```
SECRET_KEY="your key"
DEBUG=True
DATABASE_URL=yoururl
```

---

### Usage

Run the Django development server:

```bash
python manage.py runserver
```



---

### Dependencies

* Django
* Django REST Framework
* python-decouple

Install them all with:

```bash
pip install -r requirements.txt
```

---


