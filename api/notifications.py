# api/notifications.py — call this from any view to push a notification

from api.firebase import db, SERVER_TS

NOTIFICATIONS = "notifications"


def push_notification(uid: str, title: str, message: str, ntype: str = "general"):
    """
    Fire-and-forget helper. Call from any view after a meaningful action.

    Types:
        general     → default grey bell
        test        → quiz/exam events
        profile     → avatar / profile changes
        achievement → badges / milestones
    """
    try:
        db.collection(NOTIFICATIONS).add({
            "uid":        uid,
            "title":      title,
            "message":    message,
            "type":       ntype,
            "read":       False,
            "created_at": SERVER_TS,
        })
    except Exception:
        pass  # Never let a notification failure break the main flow