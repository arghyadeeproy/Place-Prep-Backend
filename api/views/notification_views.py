# api/views/notification_views.py — Notification views

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.firebase import db, SERVER_TS, Collections, doc_to_dict, query_to_list
from api.utils import success, get_uid

NOTIFICATIONS = "notifications"


class NotificationListView(APIView):
    """
    GET  /api/notifications/   → last 5 notifications for the authenticated user
    POST /api/notifications/   → (internal) create a notification (can be called from other views)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        uid = get_uid(request)

        try:
            query = (
                db.collection(NOTIFICATIONS)
                .where("uid", "==", uid)
                .order_by("created_at", direction="DESCENDING")
                .limit(5)
            )
            notifications = query_to_list(query)
        except Exception as e:
            return Response({"error": True, "detail": f"Failed to fetch notifications: {str(e)}"}, status=500)

        return success({"notifications": notifications})

    def post(self, request):
        """Internal endpoint to create a notification programmatically."""
        uid = get_uid(request)
        title   = request.data.get("title", "").strip()
        message = request.data.get("message", "").strip()
        ntype   = request.data.get("type", "general")   # general | test | profile | achievement

        if not title or not message:
            return Response({"error": True, "detail": "title and message are required."}, status=400)

        notif = {
            "uid":        uid,
            "title":      title,
            "message":    message,
            "type":       ntype,
            "read":       False,
            "created_at": SERVER_TS,
        }

        ref = db.collection(NOTIFICATIONS).add(notif)
        return success({"id": ref[1].id}, message="Notification created.", status_code=201)


class NotificationMarkReadView(APIView):
    """
    PATCH /api/notifications/<notif_id>/read/  → mark a single notification as read
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, notif_id):
        uid = get_uid(request)

        doc_ref = db.collection(NOTIFICATIONS).document(notif_id)
        doc = doc_ref.get()

        if not doc.exists:
            return Response({"error": True, "detail": "Notification not found."}, status=404)

        data = doc.to_dict()
        if data.get("uid") != uid:
            return Response({"error": True, "detail": "Not authorised."}, status=403)

        doc_ref.update({"read": True})
        return success({}, message="Marked as read.")


class NotificationMarkAllReadView(APIView):
    """
    PATCH /api/notifications/read-all/  → mark all notifications as read
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        uid = get_uid(request)

        try:
            query = (
                db.collection(NOTIFICATIONS)
                .where("uid", "==", uid)
                .where("read", "==", False)
                .stream()
            )
            for doc in query:
                doc.reference.update({"read": True})
        except Exception as e:
            return Response({"error": True, "detail": f"Failed to update: {str(e)}"}, status=500)

        return success({}, message="All notifications marked as read.")