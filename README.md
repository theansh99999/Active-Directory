# 🖥️ Active Directory Simulation (Flask + Bootstrap Dark Mode)

This project is a **simulation of Microsoft Active Directory** built using **Flask, SQLAlchemy, Flask-Login, Jinja2 Templates, and Bootstrap Dark Mode**.  
It demonstrates **enterprise-level identity and access management** features such as role-based login, user/group management, security policies, and admin dashboards — all in a clean dark UI.  

---

## 🎯 Objective
The aim of this project is to replicate the **core functionalities of Active Directory** in a simplified yet powerful way for learning and demonstration purposes.  
It is designed for:  
- 🎓 Students who want hands-on practice with authentication & authorization systems  
- 🧑‍💻 Developers exploring **Flask + SQLAlchemy** integration  
- 🏢 Professionals demonstrating **system security and directory management concepts** in interviews or portfolios  

---

## 🚀 Key Features

### 🔐 Authentication & Access Control
- Secure login system with **Flask-Login**  
- Role-based dashboards:  
  - **Admin** → Full access to management tools  
  - **User** → Limited personal access only  
- Account lockouts after multiple failed attempts  
- Password policy enforcement (minimum length, uppercase, numeric)  

---

### 👥 User Management
- Add, update, delete users  
- Password reset by admins  
- Personal profile view & update for users  
- Activity tracking for user actions  

---

### 👤 Group & Role Management
- Create and manage groups  
- Assign/remove users from groups  
- Define and modify role permissions  
- Admins can delegate access to other users  

---

### 🛡️ Security & Policy Enforcement
- Passwords stored in **hashed form (Werkzeug security)**  
- Failed login attempt tracking + temporary account lockouts  
- Role-based restrictions for sensitive actions  
- Audit logs to monitor admin/user activities  

---

### 🖥️ System Simulation
- Admin can **add/remove/disable “computers”** in the directory (simulation of real AD computer objects)  
- Option to mark computers as **online/offline/restarted**  
- Ability to delete or reset computer records for cleanup  

---

### 📊 Admin Dashboard
- Full overview of users, groups, and computers  
- Quick actions: reset password, assign role, lock/unlock user  
- Analytics view: number of users, groups, computers active  
- Manage permissions dynamically  

---

### 🎨 UI/UX (Dark Mode)
- Built with **Bootstrap 5 Dark Theme**  
- Consistent dark mode interface (permanent, no toggle)  
- Responsive design for desktop & mobile  
- Flash alerts for success/error messages  
- Clean navigation for Admins vs Users  

---

## 🏗️ Tech Stack
- **Backend:** Flask, Flask-Login, SQLAlchemy  
- **Frontend:** Jinja2 Templates + Bootstrap (Dark Theme)  
- **Database:** SQLite  
- **Security:** Password hashing (Werkzeug), role-based access  

---

## 📂 Project Structure
```
├── app.py # Main Flask application
├── models.py # Database models (User, Group, Computer)
├── templates/ # HTML templates
│ ├── base.html
│ ├── login.html
│ ├── admin_dashboard.html
│ ├── user_dashboard.html
│ ├── groups.html
│ └── computers.html
├── static/ # CSS/JS assets
├── logs/ # Audit & activity logs
└── README.md # Project documentation
```

---

## 📸 Screenshots (Planned)
- **Login Page (Dark Mode)**  
- **Admin Dashboard** (manage users, groups, computers)  
- **User Dashboard** (view personal data)  
- **Group Management View**  
- **System/Computer Management View**  

*(Screenshots can be added after running the project)*  

---

## 🌍 Applications
- **Learning:** Great project for students to understand directory services  
- **Portfolio:** Strong addition to resume showcasing **authentication + system design**  
- **Enterprise Simulation:** Demonstrates key IT concepts like Active Directory, user roles, and system management  
- **Security Practice:** Showcases password policies, hashing, and account lockouts  

---

## 🔮 Future Enhancements
To make the project even closer to real-world Active Directory, the following features can be added in future:  
- 🌐 **LDAP/LDAPS integration** for real enterprise directory support  
- 🔄 **API endpoints** for programmatic user/group management  
- 📡 **Real-time monitoring** of user logins and system activity  
- 📑 **Detailed audit reports** exportable as PDF/Excel  
- 🔔 **Email/Notification system** for password resets and alerts  
- ☁️ **Cloud-ready deployment** (Docker + AWS/Azure/GCP)  
- 🧠 **AI-based anomaly detection** for unusual login behavior  

---

## 👤 Author
**Ansh Kumar Rai**  
