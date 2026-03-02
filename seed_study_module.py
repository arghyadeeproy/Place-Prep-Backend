"""
seed_new_subjects.py
Adds 8 new subjects to Firestore:
  system-design, lld, python, java, cpp, c, cloud, ml

Run from your Django project root:
    python seed_new_subjects.py

Safe to run multiple times — uses merge=True (upsert).
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
    django.setup()
except Exception:
    pass

from api.firebase import db, Collections, SERVER_TS

NEW_MODULES = [

    # ── System Design (subject_id: "system-design") ───────────
    {"id": "scalability",    "subject_id": "system-design", "subject_name": "System Design", "title": "Scalability Basics",           "icon": "📈", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "load-balancing", "subject_id": "system-design", "subject_name": "System Design", "title": "Load Balancing & Caching",     "icon": "⚖️", "difficulty": "Medium", "lesson_count": 6},
    {"id": "databases",      "subject_id": "system-design", "subject_name": "System Design", "title": "Databases at Scale",           "icon": "🗄️", "difficulty": "Medium", "lesson_count": 6},
    {"id": "microservices",  "subject_id": "system-design", "subject_name": "System Design", "title": "Microservices Architecture",   "icon": "🔧", "difficulty": "Hard",   "lesson_count": 7},
    {"id": "cap-theorem",    "subject_id": "system-design", "subject_name": "System Design", "title": "CAP Theorem & Consistency",    "icon": "📐", "difficulty": "Hard",   "lesson_count": 5},
    {"id": "message-queues", "subject_id": "system-design", "subject_name": "System Design", "title": "Message Queues & Kafka",       "icon": "📨", "difficulty": "Hard",   "lesson_count": 5},
    {"id": "url-shortener",  "subject_id": "system-design", "subject_name": "System Design", "title": "Design URL Shortener",         "icon": "🔗", "difficulty": "Medium", "lesson_count": 4},
    {"id": "twitter",        "subject_id": "system-design", "subject_name": "System Design", "title": "Design Twitter / Instagram",   "icon": "🐦", "difficulty": "Hard",   "lesson_count": 5},

    # ── Low Level Design (subject_id: "lld") ──────────────────
    {"id": "solid",          "subject_id": "lld", "subject_name": "Low Level Design", "title": "SOLID Principles",              "icon": "🧱", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "uml",            "subject_id": "lld", "subject_name": "Low Level Design", "title": "UML & Class Diagrams",          "icon": "📊", "difficulty": "Easy",   "lesson_count": 4},
    {"id": "creational",     "subject_id": "lld", "subject_name": "Low Level Design", "title": "Creational Design Patterns",    "icon": "🏗️", "difficulty": "Medium", "lesson_count": 6},
    {"id": "structural",     "subject_id": "lld", "subject_name": "Low Level Design", "title": "Structural Design Patterns",    "icon": "🔩", "difficulty": "Medium", "lesson_count": 6},
    {"id": "behavioral",     "subject_id": "lld", "subject_name": "Low Level Design", "title": "Behavioral Design Patterns",    "icon": "🎭", "difficulty": "Hard",   "lesson_count": 7},
    {"id": "parking-lot",    "subject_id": "lld", "subject_name": "Low Level Design", "title": "Design Parking Lot System",     "icon": "🚗", "difficulty": "Medium", "lesson_count": 4},
    {"id": "booking-system", "subject_id": "lld", "subject_name": "Low Level Design", "title": "Design Booking System",         "icon": "🎟️", "difficulty": "Hard",   "lesson_count": 5},

    # ── Python (subject_id: "python") ─────────────────────────
    {"id": "basics",         "subject_id": "python", "subject_name": "Python", "title": "Python Basics & Syntax",        "icon": "🐍", "difficulty": "Easy",   "lesson_count": 6},
    {"id": "data-types",     "subject_id": "python", "subject_name": "Python", "title": "Data Types & Collections",      "icon": "📦", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "functions",      "subject_id": "python", "subject_name": "Python", "title": "Functions & Lambdas",           "icon": "⚡", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "oop",            "subject_id": "python", "subject_name": "Python", "title": "OOP in Python",                 "icon": "🧩", "difficulty": "Medium", "lesson_count": 6},
    {"id": "decorators",     "subject_id": "python", "subject_name": "Python", "title": "Decorators & Generators",       "icon": "🎨", "difficulty": "Medium", "lesson_count": 5},
    {"id": "concurrency",    "subject_id": "python", "subject_name": "Python", "title": "Multithreading & Async",        "icon": "🔄", "difficulty": "Hard",   "lesson_count": 6},
    {"id": "file-io",        "subject_id": "python", "subject_name": "Python", "title": "File I/O & Exception Handling", "icon": "📁", "difficulty": "Easy",   "lesson_count": 4},

    # ── Java (subject_id: "java") ─────────────────────────────
    {"id": "basics",         "subject_id": "java", "subject_name": "Java", "title": "Java Basics & JVM",             "icon": "☕", "difficulty": "Easy",   "lesson_count": 6},
    {"id": "oop",            "subject_id": "java", "subject_name": "Java", "title": "OOP in Java",                   "icon": "🧩", "difficulty": "Easy",   "lesson_count": 6},
    {"id": "collections",    "subject_id": "java", "subject_name": "Java", "title": "Collections Framework",         "icon": "📦", "difficulty": "Medium", "lesson_count": 7},
    {"id": "generics",       "subject_id": "java", "subject_name": "Java", "title": "Generics & Wildcards",          "icon": "🔣", "difficulty": "Medium", "lesson_count": 5},
    {"id": "streams",        "subject_id": "java", "subject_name": "Java", "title": "Streams & Lambda (Java 8+)",    "icon": "🌊", "difficulty": "Medium", "lesson_count": 6},
    {"id": "concurrency",    "subject_id": "java", "subject_name": "Java", "title": "Multithreading & Concurrency",  "icon": "🔄", "difficulty": "Hard",   "lesson_count": 7},
    {"id": "exception",      "subject_id": "java", "subject_name": "Java", "title": "Exception Handling & I/O",      "icon": "⚠️", "difficulty": "Easy",   "lesson_count": 4},

    # ── C++ (subject_id: "cpp") ───────────────────────────────
    {"id": "basics",         "subject_id": "cpp", "subject_name": "C++", "title": "C++ Basics & Syntax",           "icon": "⚙️", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "pointers",       "subject_id": "cpp", "subject_name": "C++", "title": "Pointers & References",         "icon": "👉", "difficulty": "Medium", "lesson_count": 6},
    {"id": "oop",            "subject_id": "cpp", "subject_name": "C++", "title": "OOP in C++",                    "icon": "🧩", "difficulty": "Medium", "lesson_count": 6},
    {"id": "stl",            "subject_id": "cpp", "subject_name": "C++", "title": "STL — Vectors, Maps, Sets",     "icon": "📚", "difficulty": "Medium", "lesson_count": 6},
    {"id": "templates",      "subject_id": "cpp", "subject_name": "C++", "title": "Templates & Generic Prog.",     "icon": "🔣", "difficulty": "Hard",   "lesson_count": 5},
    {"id": "memory",         "subject_id": "cpp", "subject_name": "C++", "title": "Memory Management & RAII",      "icon": "🧠", "difficulty": "Hard",   "lesson_count": 6},
    {"id": "modern-cpp",     "subject_id": "cpp", "subject_name": "C++", "title": "Modern C++ (11/14/17)",         "icon": "🚀", "difficulty": "Hard",   "lesson_count": 6},

    # ── C (subject_id: "c") ───────────────────────────────────
    {"id": "basics",         "subject_id": "c", "subject_name": "C Programming", "title": "C Basics & Syntax",             "icon": "🔤", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "pointers",       "subject_id": "c", "subject_name": "C Programming", "title": "Pointers & Arrays",             "icon": "👉", "difficulty": "Medium", "lesson_count": 6},
    {"id": "functions",      "subject_id": "c", "subject_name": "C Programming", "title": "Functions & Recursion",         "icon": "🔁", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "structs",        "subject_id": "c", "subject_name": "C Programming", "title": "Structs & Unions",              "icon": "🏗️", "difficulty": "Medium", "lesson_count": 5},
    {"id": "memory",         "subject_id": "c", "subject_name": "C Programming", "title": "Dynamic Memory (malloc/free)",  "icon": "🧠", "difficulty": "Hard",   "lesson_count": 5},
    {"id": "file-io",        "subject_id": "c", "subject_name": "C Programming", "title": "File I/O & Preprocessors",      "icon": "📁", "difficulty": "Medium", "lesson_count": 4},

    # ── Cloud Computing (subject_id: "cloud") ─────────────────
    {"id": "intro",          "subject_id": "cloud", "subject_name": "Cloud Computing", "title": "Cloud Fundamentals & Models",   "icon": "☁️", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "aws-core",       "subject_id": "cloud", "subject_name": "Cloud Computing", "title": "AWS Core Services",             "icon": "🟠", "difficulty": "Medium", "lesson_count": 7},
    {"id": "networking",     "subject_id": "cloud", "subject_name": "Cloud Computing", "title": "Cloud Networking & VPC",        "icon": "🌐", "difficulty": "Medium", "lesson_count": 6},
    {"id": "storage",        "subject_id": "cloud", "subject_name": "Cloud Computing", "title": "Storage & Databases in Cloud",  "icon": "🗄️", "difficulty": "Medium", "lesson_count": 6},
    {"id": "containers",     "subject_id": "cloud", "subject_name": "Cloud Computing", "title": "Containers & Kubernetes",       "icon": "🐳", "difficulty": "Hard",   "lesson_count": 7},
    {"id": "serverless",     "subject_id": "cloud", "subject_name": "Cloud Computing", "title": "Serverless & Lambda",           "icon": "⚡", "difficulty": "Medium", "lesson_count": 5},
    {"id": "devops",         "subject_id": "cloud", "subject_name": "Cloud Computing", "title": "CI/CD & DevOps Practices",      "icon": "🔄", "difficulty": "Hard",   "lesson_count": 6},

    # ── Basic ML (subject_id: "ml") ───────────────────────────
    {"id": "intro",          "subject_id": "ml", "subject_name": "Basic Machine Learning", "title": "ML Fundamentals & Types",       "icon": "🤖", "difficulty": "Easy",   "lesson_count": 5},
    {"id": "regression",     "subject_id": "ml", "subject_name": "Basic Machine Learning", "title": "Linear & Logistic Regression",  "icon": "📈", "difficulty": "Easy",   "lesson_count": 6},
    {"id": "classification", "subject_id": "ml", "subject_name": "Basic Machine Learning", "title": "Classification Algorithms",     "icon": "🏷️", "difficulty": "Medium", "lesson_count": 6},
    {"id": "clustering",     "subject_id": "ml", "subject_name": "Basic Machine Learning", "title": "Clustering (K-Means, DBSCAN)",  "icon": "🔵", "difficulty": "Medium", "lesson_count": 5},
    {"id": "trees",          "subject_id": "ml", "subject_name": "Basic Machine Learning", "title": "Decision Trees & Random Forest","icon": "🌳", "difficulty": "Medium", "lesson_count": 6},
    {"id": "evaluation",     "subject_id": "ml", "subject_name": "Basic Machine Learning", "title": "Model Evaluation & Metrics",    "icon": "📊", "difficulty": "Medium", "lesson_count": 5},
    {"id": "neural-nets",    "subject_id": "ml", "subject_name": "Basic Machine Learning", "title": "Intro to Neural Networks",      "icon": "🧠", "difficulty": "Hard",   "lesson_count": 7},
    {"id": "feature-eng",    "subject_id": "ml", "subject_name": "Basic Machine Learning", "title": "Feature Engineering",          "icon": "🔧", "difficulty": "Hard",   "lesson_count": 5},
]


def seed():
    col = db.collection(Collections.STUDY_MODULES)

    print(f"🌱 Seeding {len(NEW_MODULES)} new modules across 8 subjects...\n")

    by_subject = {}
    for mod in NEW_MODULES:
        by_subject.setdefault(mod["subject_id"], []).append(mod)

    total = 0
    for subject_id, mods in by_subject.items():
        print(f"📚 {subject_id.upper()} ({len(mods)} modules)")
        for mod in mods:
            doc_id = f"{subject_id}_{mod['id']}"
            col.document(doc_id).set({
                "subject_id":   mod["subject_id"],
                "subject_name": mod["subject_name"],
                "title":        mod["title"],
                "icon":         mod["icon"],
                "difficulty":   mod["difficulty"],
                "lesson_count": mod["lesson_count"],
                "created_at":   SERVER_TS,
            }, merge=True)
            print(f"   ✅ {doc_id} — {mod['title']}")
            total += 1
        print()

    print(f"🎉 Done! {total} modules seeded.")


if __name__ == "__main__":
    seed()