from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from api.firebase import db, Collections, SERVER_TS, doc_to_dict
from api.groq_ai import generate_study_module_lessons
from api.utils import success, get_uid


# ─────────────────────────────────────────
# 📚 Get Modules by Subject (Predefined)
# ─────────────────────────────────────────

class StudyModulesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, subject_id):
        modules = (
            db.collection(Collections.STUDY_MODULES)
            .where("subject_id", "==", subject_id)
            .stream()
        )

        data = []
        for doc in modules:
            item = doc.to_dict()
            item["id"] = doc.id
            data.append(item)

        return success(data)


# ─────────────────────────────────────────
# 📖 Get Module Lessons (Generate if Missing)
# ─────────────────────────────────────────

class StudyModuleDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, subject_id, module_id):

        module_ref = db.collection(Collections.STUDY_MODULES).document(module_id)
        module_doc = module_ref.get()

        if not module_doc.exists:
            return Response({"error": True, "detail": "Module not found."}, status=404)

        module_data = module_doc.to_dict()

        # 🔎 Fetch existing lessons
        lessons_query = (
            db.collection(Collections.STUDY_LESSONS)
            .where("module_id", "==", module_id)
            .order_by("order")
            .stream()
        )

        lessons = [doc.to_dict() for doc in lessons_query]

        # 🔥 If no lessons → generate using AI
        if not lessons:
            try:
                generated = generate_study_module_lessons(
                    subject_name=module_data.get("subject_name", subject_id),
                    module_title=module_data["title"],
                    lesson_count=module_data["lesson_count"],
                )
            except ValueError as e:
                return Response({"error": True, "detail": str(e)}, status=400)

            # Store lessons
            for lesson in generated:
                db.collection(Collections.STUDY_LESSONS).add({
                    "subject_id": subject_id,
                    "module_id": module_id,
                    "title": lesson["title"],
                    "type": lesson["type"],
                    "content": lesson["content"],
                    "order": lesson["order"],
                    "created_at": SERVER_TS,
                    "ai_generated": True,
                })

            # Re-fetch
            lessons_query = (
                db.collection(Collections.STUDY_LESSONS)
                .where("module_id", "==", module_id)
                .order_by("order")
                .stream()
            )
            lessons = [doc.to_dict() for doc in lessons_query]

        return success({
            "module": module_data,
            "lessons": lessons
        })


# ─────────────────────────────────────────
# ✅ Mark Lesson Completed
# ─────────────────────────────────────────

class MarkLessonCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, module_id):
        uid = get_uid(request)
        lesson_order = request.data.get("lesson_order")

        if not lesson_order:
            raise ValidationError("lesson_order is required")

        progress_ref = db.collection(Collections.USER_PROGRESS).document(
            f"{uid}_{module_id}"
        )

        snapshot = progress_ref.get()

        if snapshot.exists:
            data = snapshot.to_dict()
            completed = set(data.get("completed_lessons", []))
        else:
            completed = set()

        completed.add(int(lesson_order))

        progress_ref.set({
            "user_id": uid,
            "module_id": module_id,
            "completed_lessons": list(completed),
            "updated_at": SERVER_TS,
        })

        # 🔥 If module fully completed → increment modules_done
        module_doc = db.collection(Collections.STUDY_MODULES).document(module_id).get()
        if module_doc.exists:
            lesson_count = module_doc.to_dict()["lesson_count"]

            if len(completed) >= lesson_count:
                user_ref = db.collection(Collections.USERS).document(uid)
                user_ref.update({
                    "stats.modules_done": firestore.Increment(1)
                })

        return success({"completed_lessons": list(completed)})