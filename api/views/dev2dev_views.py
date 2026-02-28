"""api/views/dev2dev_views.py — Dev2Dev community Q&A."""

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from google.cloud import firestore as gfs

from api.firebase import db, SERVER_TS, Collections, doc_to_dict, query_to_list
from api.utils import success, paginate, get_uid, get_user_info


# ── Posts ─────────────────────────────────────────────────────────────────────

class PostListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tag  = request.query_params.get("tag", "All")
        page = int(request.query_params.get("page", 1))

        query = db.collection(Collections.POSTS).order_by("created_at", direction=gfs.Query.DESCENDING)
        if tag and tag != "All":
            query = query.where("tags", "array_contains", tag)

        posts = query_to_list(query)
        for p in posts:
            p.pop("likes", None)   # don't leak UID lists

        return success(paginate(posts, page=page))

    def post(self, request):
        title = request.data.get("title", "").strip()
        body  = request.data.get("body", "").strip()
        tags  = request.data.get("tags", [])

        if not title or not body:
            return Response({"error": True, "detail": "title and body are required."}, status=400)

        user = get_user_info(request)
        ref  = db.collection(Collections.POSTS).document()
        doc  = {
            "title":           title,
            "body":            body,
            "tags":            tags if isinstance(tags, list) else [],
            "author_uid":      user["uid"],
            "author_name":     user["name"],
            "author_initials": user["initials"],
            "likes":           [],
            "like_count":      0,
            "comment_count":   0,
            "created_at":      SERVER_TS,
        }
        ref.set(doc)
        db.collection(Collections.USERS).document(user["uid"]).update({
        "stats.posts": gfs.Increment(1)
        })

        # Re-fetch so SERVER_TS becomes real timestamp
        saved = doc_to_dict(ref.get())
        saved.pop("likes", None)

        return success(saved, message="Question posted.", status_code=201)


class PostDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id: str):
        doc = doc_to_dict(db.collection(Collections.POSTS).document(post_id).get())
        if not doc:
            return Response({"error": True, "detail": "Post not found."}, status=404)
        uid = get_uid(request)
        doc["liked_by_me"] = uid in doc.get("likes", [])
        doc.pop("likes", None)
        return success(doc)

    def delete(self, request, post_id: str):
        uid = get_uid(request)
        ref = db.collection(Collections.POSTS).document(post_id)
        doc = doc_to_dict(ref.get())
        if not doc:
            return Response({"error": True, "detail": "Post not found."}, status=404)
        if doc["author_uid"] != uid:
            return Response({"error": True, "detail": "Forbidden."}, status=403)
        for c in ref.collection("comments").stream():
            c.reference.delete()
        ref.delete()
        db.collection(Collections.USERS).document(uid).update({"stats.posts": gfs.Increment(-1)})
        return success(message="Post deleted.")


class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id: str):
        uid = get_uid(request)
        ref = db.collection(Collections.POSTS).document(post_id)
        doc = doc_to_dict(ref.get())
        if not doc:
            return Response({"error": True, "detail": "Post not found."}, status=404)
        likes = doc.get("likes", [])
        if uid in likes:
            likes.remove(uid); liked = False
        else:
            likes.append(uid); liked = True
        ref.update({"likes": likes, "like_count": len(likes)})
        return success({"liked": liked, "like_count": len(likes)})


# ── Comments ──────────────────────────────────────────────────────────────────

class CommentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id: str):
        uid = get_uid(request)
        if not db.collection(Collections.POSTS).document(post_id).get().exists:
            return Response({"error": True, "detail": "Post not found."}, status=404)

        comments = query_to_list(
            db.collection(Collections.POSTS).document(post_id)
              .collection("comments").order_by("created_at")
        )
        for c in comments:
            c["liked_by_me"]   = uid in c.get("likes", [])
            c["upvoted_by_me"] = uid in c.get("upvotes", [])
            c.pop("likes", None)
            c.pop("upvotes", None)
        return success(comments)

    def post(self, request, post_id: str):
        body = request.data.get("body", "").strip()
        if not body:
            return Response({"error": True, "detail": "body is required."}, status=400)

        post_ref = db.collection(Collections.POSTS).document(post_id)
        if not post_ref.get().exists:
            return Response({"error": True, "detail": "Post not found."}, status=404)

        user = get_user_info(request)
        ref  = post_ref.collection("comments").document()
        doc  = {
            "body":            body,
            "author_uid":      user["uid"],
            "author_name":     user["name"],
            "author_initials": user["initials"],
            "likes":           [],
            "like_count":      0,
            "upvotes":         [],
            "upvote_count":    0,
            "created_at":      SERVER_TS,
        }
        ref.set(doc)
        post_ref.update({"comment_count": gfs.Increment(1)})
        db.collection(Collections.USERS).document(user["uid"]).update({
            "stats.comments": gfs.Increment(1)
        })

        # Re-fetch so SERVER_TS resolves
        saved = doc_to_dict(ref.get())
        saved.pop("likes", None)
        saved.pop("upvotes", None)
        saved["liked_by_me"] = False
        saved["upvoted_by_me"] = False

        return success(saved, status_code=201)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, post_id: str, comment_id: str):
        uid         = get_uid(request)
        post_ref    = db.collection(Collections.POSTS).document(post_id)
        comment_ref = post_ref.collection("comments").document(comment_id)
        doc = doc_to_dict(comment_ref.get())
        if not doc:
            return Response({"error": True, "detail": "Comment not found."}, status=404)
        if doc["author_uid"] != uid:
            return Response({"error": True, "detail": "Forbidden."}, status=403)
        comment_ref.delete()
        post_ref.update({"comment_count": gfs.Increment(-1)})
        db.collection(Collections.USERS).document(uid).update({"stats.comments": gfs.Increment(-1)})
        return success(message="Comment deleted.")


class CommentLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id: str, comment_id: str):
        uid = get_uid(request)
        ref = db.collection(Collections.POSTS).document(post_id).collection("comments").document(comment_id)
        doc = doc_to_dict(ref.get())
        if not doc:
            return Response({"error": True, "detail": "Comment not found."}, status=404)
        likes = doc.get("likes", [])
        if uid in likes:
            likes.remove(uid); liked = False
        else:
            likes.append(uid); liked = True
        ref.update({"likes": likes, "like_count": len(likes)})
        return success({"liked": liked, "like_count": len(likes)})


class CommentUpvoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id: str, comment_id: str):
        uid = get_uid(request)
        ref = db.collection(Collections.POSTS).document(post_id).collection("comments").document(comment_id)
        doc = doc_to_dict(ref.get())
        if not doc:
            return Response({"error": True, "detail": "Comment not found."}, status=404)
        upvotes = doc.get("upvotes", [])
        if uid in upvotes:
            upvotes.remove(uid); upvoted = False
        else:
            upvotes.append(uid); upvoted = True
        ref.update({"upvotes": upvotes, "upvote_count": len(upvotes)})
        return success({"upvoted": upvoted, "upvote_count": len(upvotes)})