import json
import re
import random
import time
from groq import Groq
from django.conf import settings


client = Groq(api_key=settings.GROQ_API_KEY)

MODEL = "llama-3.3-70b-versatile"


def _clean_json(raw: str) -> str:
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


# ─────────────────────────────────────────
# Company Guide  (fully AI-generated, company-specific)
# ─────────────────────────────────────────

def generate_company_guide(company_name: str) -> dict:
    seed = f"{int(time.time() * 1000) % 99999}_{random.randint(1000, 9999)}"

    prompt = f"""
You are a senior placement expert with verified knowledge of {company_name}'s actual hiring process.
Session seed: {seed}

Generate a DETAILED, 100% COMPANY-SPECIFIC interview preparation guide for: {company_name}

════════════════════════════════════════
ABSOLUTE RULES — every single one is mandatory:
════════════════════════════════════════

1. PYQS MUST BE REAL, COMPANY-SPECIFIC questions:
   - These must be questions that have ACTUALLY been asked at {company_name} interviews,
     sourced from verified platforms like GeeksForGeeks, LeetCode Discuss, Glassdoor,
     AmbitionBox, or InterviewBit.
   - Do NOT generate generic DSA questions like "Reverse a linked list" or "Two Sum"
     unless they are specifically and frequently documented for {company_name}.
   - For product/FAANG companies (Google, Amazon, Meta, Microsoft, Adobe, Oracle, Goldman Sachs, D.E. Shaw):
     * Include their specific algorithmic problems with exact problem descriptions
     * Include system design questions they actually ask (e.g. "Design Google Search", "Design Amazon's recommendation system")
     * Include behavioral/LP questions unique to their culture
   - For service companies (TCS, Infosys, Wipro, Capgemini, Accenture, Deloitte):
     * Include their specific OA test questions (NQT patterns, AMCAT, Cocubes)
     * Include the specific pseudocode/output-tracing questions they use
     * Include their specific aptitude question patterns
   - For fintech/startup companies (Swiggy, Zomato, Paytm, PhonePe):
     * Include their specific system design questions (e.g. "Design Swiggy's delivery tracking")
     * Include their product-specific questions
   - Generate at least 8-10 PYQs with different tags

2. ROUNDS must reflect {company_name}'s ACTUAL interview process:
   - Use the real round names (e.g. "TCS NQT", "Amazon Bar Raiser", "Google Onsite", "Infosys HackWithInfy")
   - Use real platform names (HackerRank for Amazon OA, Codility for Microsoft, etc.)
   - Use real durations and formats
   - Include the correct number of rounds

3. TIPS must be {company_name}-SPECIFIC:
   - Mention their actual evaluation criteria
   - Mention their specific culture/values (Amazon Leadership Principles, Google Googleyness, etc.)
   - Mention their specific interview quirks or known patterns

4. TAGLINE must be witty and specific to {company_name}, not generic.

5. Every field must be accurate and non-generic. If you are uncertain about a detail,
   use the most commonly reported version from interview experience databases.

════════════════════════════════════════
Return ONLY valid JSON matching this exact schema (no extra text, no markdown):
════════════════════════════════════════

{{
  "name": "{company_name}",
  "tagline": "<witty, {company_name}-specific tagline>",
  "about": "<2–3 sentences specific to {company_name}'s interview culture and what they look for>",
  "package": "<realistic salary range in LPA for India fresher/SDE-1>",
  "difficulty": "Easy | Medium | Hard",
  "rounds": <integer — actual number of rounds>,
  "roles": ["<actual roles {company_name} hires for>"],
  "rounds_detail_list": [
    {{
      "name": "<actual round name>",
      "type": "OA | Technical | HR | Behavioral | System",
      "duration": "<real duration>",
      "desc": "<specific description of what happens in this round at {company_name}>"
    }}
  ],
  "pyqs": [
    {{
      "q": "<actual question asked at {company_name} — specific, not generic>",
      "tag": "<topic tag>",
      "difficulty": "Easy | Medium | Hard",
      "freq": "High | Medium | Low"
    }}
  ],
  "tips": ["<company-specific tip>"],
  "resources": [
    {{ "title": "<resource name>", "type": "Practice | Book | Guide | PYQ | Video" }}
  ]
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,   # Lower temp for factual accuracy
    )

    raw = _clean_json(response.choices[0].message.content)

    try:
        return json.loads(raw)
    except Exception as e:
        raise ValueError(f"Groq invalid JSON: {e}\nRaw: {raw[:400]}")


# ─────────────────────────────────────────
# Topic subtopics map — forces variety in MCQ generation
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
    subtopics = _TOPIC_SUBTOPICS.get(topic, [topic])
    chosen_subtopics = random.sample(subtopics, min(count, len(subtopics)))
    while len(chosen_subtopics) < count:
        chosen_subtopics.append(random.choice(subtopics))

    chosen_angles = [random.choice(_QUESTION_ANGLES) for _ in range(count)]
    seed_token = f"{int(time.time() * 1000) % 99999}_{random.randint(1000, 9999)}"

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
        temperature=0.95,
        seed=random.randint(1, 2**31 - 1),
    )

    raw = _clean_json(response.choices[0].message.content)

    try:
        questions = json.loads(raw)
    except Exception as e:
        raise ValueError(f"Groq bad JSON: {e}\nRaw: {raw[:400]}")

    if not isinstance(questions, list):
        raise ValueError("Expected list of questions")

    seen_questions: set[str] = set()
    unique = []
    for q in questions:
        key = q.get("question", "").strip().lower()[:80]
        if key not in seen_questions:
            seen_questions.add(key)
            unique.append(q)

    return unique