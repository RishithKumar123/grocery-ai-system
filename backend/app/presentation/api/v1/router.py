from fastapi import APIRouter
from app.presentation.api.v1.auth import router as auth_router
from app.presentation.api.v1.inventory import router as inventory_router
from app.presentation.api.v1.protected import router as protected_router
from app.presentation.api.v1.products import router as products_router
from app.presentation.api.v1.suppliers import router as suppliers_router
from app.presentation.api.v1.stores import router as stores_router
from app.presentation.api.v1.videos import router as videos_router
from app.presentation.api.v1.ai_scans import router as ai_scans_router
from app.presentation.api.v1.reports import router as reports_router
from app.presentation.api.v1.vendor import router as vendor_router
from app.presentation.api.v1.shopkeeper import router as shopkeeper_router
from app.presentation.api.v1.dataset import router as dataset_router
from app.presentation.api.v1.categories import router as categories_router
from app.presentation.api.v1.brands import router as brands_router
from app.presentation.api.v1.layout import router as layout_router
from app.presentation.api.v1.stock_transactions import router as stock_transactions_router
from app.presentation.api.v1.annotations import router as annotations_router
from app.presentation.api.v1.dashboard import router as dashboard_router
from app.presentation.api.v1.preprocessing import router as preprocessing_router
from app.presentation.api.v1.validation import router as validation_router
from app.presentation.api.v1.model_registry import router as model_registry_router
from app.presentation.api.v1.training import router as training_router
from app.presentation.api.v1.inference import router as inference_router
from app.presentation.api.v1.barcode import router as barcode_router
from app.presentation.api.v1.recognition import router as recognition_router
from app.presentation.api.v1.decision_router import router as decisions_router
from app.presentation.api.v1.counting_router import router as counting_router
from app.presentation.api.v1.location_router import router as location_router
from app.presentation.api.v1.inventory_update_router import router as inventory_update_router
from app.presentation.api.v1.availability_router import router as availability_router
from app.presentation.api.v1.product_verification import router as product_verification_router
from app.presentation.api.v1.verification import router as verification_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(inventory_router)
api_router.include_router(protected_router)
api_router.include_router(products_router)
api_router.include_router(suppliers_router)
api_router.include_router(stores_router)
api_router.include_router(videos_router)
api_router.include_router(ai_scans_router)
api_router.include_router(reports_router)
api_router.include_router(vendor_router)
api_router.include_router(shopkeeper_router)
api_router.include_router(dataset_router)
api_router.include_router(categories_router)
api_router.include_router(brands_router)
api_router.include_router(layout_router)
api_router.include_router(stock_transactions_router)
api_router.include_router(annotations_router)
api_router.include_router(preprocessing_router)
api_router.include_router(validation_router)
api_router.include_router(model_registry_router)
api_router.include_router(training_router)
api_router.include_router(inference_router)
api_router.include_router(barcode_router)
api_router.include_router(recognition_router)
api_router.include_router(decisions_router)
api_router.include_router(counting_router)
api_router.include_router(location_router)
api_router.include_router(inventory_update_router)
api_router.include_router(availability_router)
api_router.include_router(dashboard_router)
api_router.include_router(product_verification_router)
api_router.include_router(verification_router)
