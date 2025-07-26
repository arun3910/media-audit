# 📰 MediaAudit – News Bias & Summary Engine

**MediaAudit** is a Flask-based web application designed to help journalists, editors, and researchers quickly analyze news articles for **bias**, **tone**, **emotion**, and **framing**. It also provides **rewrites**, **fact-checking summaries**, and **headline suggestions** using OpenAI's GPT models.

---

## 🔍 Features

- 🧠 **AI-Powered Article Analysis**
  - Detects **bias** and **framing style**
  - Classifies **tone** and emotional impact
  - Generates **balanced rewrites** of news stories

- ✍️ **Rewrite Assistant**
  - Produces clearer, neutral versions of submitted content
  - Highlights word-level changes with color-coded diffs

- 🎯 **Headline Generator**
  - Suggests one engaging headline and two A/B testing variants

- 🧾 **Framing & Tone Analysis**
  - Breaks down how different reader groups might perceive an article
  - Suggests adjustments for broader appeal

- ✅ **Fact-Checking Summaries**
  - Extracts and verifies major claims from the article
  - Displays findings in reader-friendly format

- 📊 **Emotion Analysis**
  - Quantifies emotional tone (anger, joy, fear, surprise)

---

## 🧱 Tech Stack

- **Backend:** Python, Flask, SQLAlchemy
- **Frontend:** Bootstrap, HTML5, Jinja2
- **AI Integration:** OpenAI API (GPT-4o fallback to GPT-3.5)
- **Database:** MySQL (via SQLAlchemy ORM)

---

## ⚙️ Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/mediaaudit.git
cd mediaaudit
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up MySQL Database

Create a new MySQL database using a tool like MySQL Workbench or CLI:

```sql
CREATE DATABASE my_base_app;
```

---

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_NAME=my_base_app
SECRET_KEY=your-secret-key
```

Replace `yourpassword` and `your-secret-key` as needed.

---

### 6. Initialize the Database with Alembic

Set your Flask app environment variable:
```bash
$env:FLASK_APP="run.py"      # PowerShell (Windows)
# OR
export FLASK_APP=run.py      # macOS/Linux
```

Then run:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

This will create the `users` table in your database.

---

### 7. Insert a Super Admin User

Use Python to generate a hashed password:
```python
from werkzeug.security import generate_password_hash
print(generate_password_hash("admin"))
```

Then use this SQL (replace the hash with yours):
```sql
INSERT INTO users (name, username, password, role, created_at)
VALUES ('Admin', 'admin', 'your_hashed_password_here', 'super_admin', NOW());
```

---

### 8. Run the App

```bash
flask run
```

Visit `http://localhost:5000` in your browser.

---

## 🧪 Folder Structure

```
mediaaudit/
├── app.py
├── routes.py
├── models.py
├── services/
│   ├── ai_utils.py
├── templates/
│   ├── add_user.html
│   ├── base.html
│   ├── compare.html
│   ├── dashboard.html
│   ├── login.html
│   ├── mediaaudit.html
│   ├── rewrite.html
│   └── users.html
├── static/
│   └── (CSS/JS assets)
├── migrations/
├── requirements.txt
├── config.py
├── run.py
└── README.md

```

---

## 🧠 Example Use Cases

- Editors want to **rewrite articles** to remove sensationalism.
- Journalists want **neutral rewrites** before publishing.
- Researchers want to **analyze media framing trends**.
- Students and readers want to **fact-check breaking news**.
- Platforms want **automated article evaluations** to flag bias.