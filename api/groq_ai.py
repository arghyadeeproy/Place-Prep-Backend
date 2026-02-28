import json
import re
import random
import time
from groq import Groq
from django.conf import settings


client = Groq(api_key=settings.GROQ_API_KEY)

MODEL = "llama-3.3-70b-versatile"   # Best balance for quality + JSON


def _clean_json(raw: str) -> str:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


# ─────────────────────────────────────────
# Company Guide
# ─────────────────────────────────────────

def generate_company_guide(company_name: str) -> dict:
    prompt = f"""
You are a placement preparation expert.
Generate a structured interview guide for {company_name}.

Return ONLY valid JSON.

Schema:
{{
  "name": "{company_name}",
  "tagline": "...",
  "about": "...",
  "package": "...",
  "difficulty": "Easy | Medium | Hard",
  "rounds": <integer>,
  "roles": ["..."],
  "rounds_detail_list": [
    {{
      "name": "...",
      "type": "OA | Technical | HR | Behavioral",
      "duration": "...",
      "desc": "..."
    }}
  ],
  "pyqs": [
    {{
      "q": "...",
      "tag": "...",
      "difficulty": "...",
      "freq": "High | Medium | Low"
    }}
  ],
  "tips": ["..."],
  "resources": [
    {{ "title": "...", "type": "Practice | Book | Guide" }}
  ]
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    raw = _clean_json(response.choices[0].message.content)

    try:
        return json.loads(raw)
    except Exception as e:
        raise ValueError(f"Groq invalid JSON: {e}\nRaw: {raw[:400]}")


# ─────────────────────────────────────────
# Topic subtopics map — forces variety
# ─────────────────────────────────────────

_TOPIC_SUBTOPICS = {
    "DSA": [
        "Arrays", "Linked Lists", "Stacks", "Queues", "Hash Maps",
        "Binary Trees", "BST", "Heaps", "Graphs", "Tries",
        "Dynamic Programming", "Greedy Algorithms", "Recursion & Backtracking",
        "Sorting Algorithms", "Searching Algorithms", "Sliding Window",
        "Two Pointers", "Divide and Conquer", "Bit Manipulation", "Segment Trees",
    ],
    "DBMS": [
        "Normalization (1NF–BCNF)", "ER Diagrams", "Transactions & ACID",
        "Concurrency Control", "Deadlocks", "Indexing & B-Trees",
        "Query Optimization", "Relational Algebra", "Views & Triggers",
        "Stored Procedures", "CAP Theorem", "Sharding & Partitioning",
        "OLAP vs OLTP", "Joins (Inner, Outer, Cross)", "Aggregate Functions",
    ],
    "OS": [
        "Process vs Thread", "CPU Scheduling Algorithms", "Deadlock Detection",
        "Memory Management", "Paging & Segmentation", "Virtual Memory",
        "File Systems", "Semaphores & Mutexes", "Inter-Process Communication",
        "System Calls", "Kernel vs User Mode", "Disk Scheduling",
        "Cache Memory", "Thrashing", "Booting Process",
    ],
    "CN": [
        "OSI Model Layers", "TCP vs UDP", "IP Addressing & Subnetting",
        "DNS & DHCP", "HTTP vs HTTPS", "SSL/TLS Handshake",
        "Routing Algorithms", "Congestion Control", "ARP & MAC",
        "Firewalls & NAT", "CDN", "WebSockets", "IPv4 vs IPv6",
        "Switching Techniques", "Ethernet & WiFi Protocols",
    ],
    "OOPs": [
        "Encapsulation", "Inheritance", "Polymorphism", "Abstraction",
        "Interfaces vs Abstract Classes", "Method Overriding vs Overloading",
        "Constructor & Destructor", "Static vs Instance Members",
        "Design Patterns (Singleton, Factory, Observer)",
        "SOLID Principles", "Composition vs Inheritance",
        "Access Modifiers", "Virtual Functions", "Multiple Inheritance",
    ],
    "Aptitude": [
        "Percentages", "Profit & Loss", "Time & Work", "Time, Speed & Distance",
        "Simple & Compound Interest", "Ratios & Proportions",
        "Mixtures & Allegations", "Number Series", "Permutations & Combinations",
        "Probability", "Averages", "Ages Problems", "Clocks & Calendars",
        "Blood Relations", "Logical Reasoning",
    ],
    "SQL": [
        "SELECT & WHERE Clauses", "GROUP BY & HAVING", "ORDER BY",
        "INNER JOIN / LEFT JOIN / RIGHT JOIN", "SELF JOIN", "Subqueries",
        "CTEs (WITH clause)", "Window Functions (RANK, ROW_NUMBER, LAG/LEAD)",
        "CASE Statements", "NULL Handling (COALESCE, IS NULL)",
        "String Functions", "Date Functions", "Aggregate Functions",
        "CREATE / ALTER / DROP", "INSERT / UPDATE / DELETE",
    ],
    "Python": [
        "List Comprehensions", "Generators & Iterators", "Decorators",
        "Lambda Functions", "Exception Handling", "Context Managers (with)",
        "OOP in Python", "Dunder/Magic Methods", "Multithreading vs Multiprocessing",
        "asyncio & async/await", "Python Data Model", "Modules & Packages",
        "Type Hints", "dataclasses", "collections module",
    ],
    "Java": [
        "JVM Architecture", "Garbage Collection", "Generics",
        "Collections Framework", "Exception Handling", "Java Streams API",
        "Lambda Expressions", "Multithreading & Synchronization",
        "Interface Default Methods", "Abstract Classes", "Enum",
        "String vs StringBuilder", "Java Memory Model",
        "Spring Beans & Dependency Injection", "Serialization",
    ],
    "SystemDesign": [
        "Load Balancing Strategies", "Caching (Redis, Memcached)",
        "Database Sharding", "Consistent Hashing", "Message Queues (Kafka, RabbitMQ)",
        "Microservices vs Monolith", "API Gateway", "Rate Limiting",
        "Event-Driven Architecture", "CQRS & Event Sourcing",
        "CAP Theorem in Practice", "Designing URL Shortener",
        "Designing Twitter Feed", "Designing WhatsApp",
        "Horizontal vs Vertical Scaling",
    ],
}

_QUESTION_ANGLES = [
    "definition and conceptual understanding",
    "output prediction / tracing",
    "real-world application scenario",
    "comparison between two similar concepts",
    "error / bug identification",
    "time or space complexity analysis",
    "edge case or corner case behavior",
    "best practice or anti-pattern",
    "numerical or calculation based",
    "true/false reasoning with justification",
]


# ─────────────────────────────────────────
# MCQ Generation  (anti-repeat)
# ─────────────────────────────────────────

def generate_mcq_questions(topic: str, difficulty: str, count: int = 10) -> list:
    # Pick random subtopics and question angles to force variety
    subtopics = _TOPIC_SUBTOPICS.get(topic, [topic])
    chosen_subtopics = random.sample(subtopics, min(count, len(subtopics)))
    # If count > available subtopics, fill remainder randomly
    while len(chosen_subtopics) < count:
        chosen_subtopics.append(random.choice(subtopics))

    chosen_angles = [random.choice(_QUESTION_ANGLES) for _ in range(count)]

    # Unique seed so the model sees a "fresh" context each call
    seed_token = f"{int(time.time() * 1000) % 99999}_{random.randint(1000, 9999)}"

    # Build per-question directives so the model doesn't cluster around common topics
    directives = "\n".join(
        f"  Q{i+1}: subtopic='{chosen_subtopics[i]}', angle='{chosen_angles[i]}'"
        for i in range(count)
    )

    prompt = f"""
You are a strict MCQ generator. Session seed: {seed_token}

Generate exactly {count} UNIQUE multiple-choice questions for:
  Topic:      {topic}
  Difficulty: {difficulty}

STRICT RULES — you MUST follow all of them:
1. Every question MUST come from a DIFFERENT subtopic and angle as listed below.
2. NO two questions can test the same concept or use similar wording.
3. Do NOT generate common textbook examples (e.g. no Fibonacci, no "what is OOP", no generic Hello World).
4. Questions must be specific, precise, and non-trivial for {difficulty} level.
5. Each question must have exactly 4 options — only ONE is correct.
6. The correct answer index (0-3) must be evenly distributed — do NOT always make option 0 or 1 correct.
7. Explanations must be concise (1–2 sentences) and explain WHY the answer is correct.
8. Return ONLY a valid JSON array — no extra text, no markdown fences.

Per-question assignments (strictly follow):
{directives}

JSON schema (return an array of exactly {count} objects):
[
  {{
    "question": "...",
    "options": ["option0", "option1", "option2", "option3"],
    "answer": <0|1|2|3>,
    "explanation": "...",
    "tag": "<specific subtopic>",
    "difficulty": "{difficulty}",
    "type": "conceptual | numerical | code-output | scenario | comparison"
  }}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.95,   # slightly higher than before for more variety
        seed=random.randint(1, 2**31 - 1),  # Groq supports seed param
    )

    raw = _clean_json(response.choices[0].message.content)

    try:
        questions = json.loads(raw)
    except Exception as e:
        raise ValueError(f"Groq bad JSON: {e}\nRaw: {raw[:400]}")

    if not isinstance(questions, list):
        raise ValueError("Expected list of questions")

    # Deduplicate by question text (just in case model still slips one in)
    seen_questions: set[str] = set()
    unique = []
    for q in questions:
        key = q.get("question", "").strip().lower()[:80]
        if key not in seen_questions:
            seen_questions.add(key)
            unique.append(q)

    return unique