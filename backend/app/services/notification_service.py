import os
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.data.models.notification_model import NotificationModel
from app.data.models.user_model import UserModel
from app.data.models.store_model import user_store_assignments

class NotificationService:
    @staticmethod
    def dispatch(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notif_type: str,  # "Low Stock", "Expiry", "Failed Scan", "Supplier Update"
        store_id: int = None
    ):
        """
        Dispatch a notification across three channels:
        1. Push Notification (Database model)
        2. Simulated Email Channel (stdout logs)
        3. Simulated SMS Channel (stdout logs)
        """
        # Save to DB (Push Notification repository)
        db_notif = NotificationModel(
            user_id=user_id,
            store_id=store_id,
            title=title,
            message=message,
            type=notif_type,
            is_read=False
        )
        db.add(db_notif)
        db.commit()
        db.refresh(db_notif)

        # Resolve user email and phone
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        email = user.email if user else "user@example.com"
        phone = "+1 (555) 987-6543"  # default profile phone fallback

        # 1. Simulated Email Logs
        logger.info(
            f"\n"
            f"=============================================================\n"
            f"✉️  [EMAIL DISPATCH] -> {email}\n"
            f"Subject: [{notif_type.upper()}] {title}\n"
            f"Content: {message}\n"
            f"=============================================================\n"
        )

        # 2. Simulated SMS Logs
        logger.info(
            f"\n"
            f"=============================================================\n"
            f"📱 [SMS DISPATCH] -> {phone}\n"
            f"Body: [{notif_type.upper()}] {title} - {message}\n"
            f"=============================================================\n"
        )

        return db_notif

    @staticmethod
    def notify_store_users(
        db: Session,
        store_id: int,
        title: str,
        message: str,
        notif_type: str
    ):
        """Send notification to all shopkeepers/admins assigned to a store branch."""
        assigned_users = db.query(UserModel).join(
            user_store_assignments, UserModel.id == user_store_assignments.c.user_id
        ).filter(
            user_store_assignments.c.store_id == store_id
        ).all()

        # Fallback to notify any admins if no specific store assignments exist
        if not assigned_users:
            assigned_users = db.query(UserModel).filter(UserModel.role == "Admin").all()

        for user in assigned_users:
            NotificationService.dispatch(
                db=db,
                user_id=user.id,
                title=title,
                message=message,
                notif_type=notif_type,
                store_id=store_id
            )
