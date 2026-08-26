from fastapi import APIRouter, Depends
from app.core.role_checker import RoleChecker
from app.domain.entities.user import User

router = APIRouter(prefix="/protected", tags=["role-protection-demo"])


@router.get("/admin", response_model=dict)
def get_admin_data(
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin"]))
):
    """Secure endpoint accessible only to Users with 'Admin' role."""
    return {
        "success": True,
        "message": f"Welcome, Admin {current_user.full_name}! You have accessed root administrative analytics.",
        "data": {
            "system_status": "Operational",
            "active_sessions": 42,
            "connected_vendors": 7
        }
    }


@router.get("/vendor", response_model=dict)
def get_vendor_data(
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    """Secure endpoint accessible to 'Admin' and 'Vendor' roles."""
    return {
        "success": True,
        "message": f"Welcome {current_user.full_name}! You have accessed vendor stock settings.",
        "data": {
            "incoming_shipments": 3,
            "pending_invoices": 12
        }
    }


@router.get("/shopkeeper", response_model=dict)
def get_shopkeeper_data(
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Shopkeeper"]))
):
    """Secure endpoint accessible to 'Admin' and 'Shopkeeper' roles."""
    return {
        "success": True,
        "message": f"Welcome {current_user.full_name}! You have accessed store inventory checklists.",
        "data": {
            "shelves_monitored": 18,
            "alerts_unresolved": 4
        }
    }
