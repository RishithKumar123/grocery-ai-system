import os
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.presentation.api.v1.router import api_router
from app.presentation.middleware.tracing_middleware import TracingMiddleware
from app.presentation.middleware.request_id_middleware import RequestIDMiddleware
from app.presentation.middleware.security_headers_middleware import SecurityHeadersMiddleware
from app.presentation.middleware.rate_limit_middleware import RateLimitMiddleware

# Import models for registration in SQLAlchemy Base metadata
from app.data.models.user_model import UserModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.refresh_token_model import RefreshTokenModel
from app.data.models.store_model import StoreModel
from app.data.models.product_model import ProductModel
from app.data.models.supplier_model import SupplierModel
from app.data.models.video_model import VideoModel
from app.data.models.ai_scan_model import AIScanModel, AIScanDetectionModel
from app.data.models.report_model import ReportModel
from app.data.models.order_model import OrderModel, OrderItemModel
from app.data.models.notification_model import NotificationModel
from app.data.models.audit_log_model import AuditLogModel
from app.data.models.category_model import CategoryModel
from app.data.models.brand_model import BrandModel
from app.data.models.decision_model import (
    DecisionResultModel,
    DecisionCandidateModel,
    DecisionRuleModel,
    DecisionWeightModel,
    DecisionFeedbackModel
)
from app.data.models.counting_model import (
    CountingJobModel,
    CountingResultModel,
    TrackedObjectModel,
    CountStatisticsModel,
    CountValidationModel,
    CountHistoryModel
)
from app.data.models.shelf_mapping_model import (
    StoreMapModel,
    AisleMapModel,
    RackLocationModel,
    ShelfMapModel,
    PlanogramModel,
    ProductLocationModel,
    LocationHistoryModel,
    MisplacedProductModel,
    EmptyShelfModel,
    OccupancyStatisticsModel
)
from app.data.models.inventory_update_model import (
    InventoryUpdateModel,
    InventoryAdjustmentModel,
    InventoryReconciliationModel,
    InventorySnapshotModel,
    UpdateRuleModel,
    UpdateQueueModel,
    ApprovalRequestModel,
    RollbackHistoryModel
)
from app.data.models.availability_model import (
    AvailabilityRequestModel,
    AvailabilityResultModel,
    AvailabilityHistoryModel,
    AvailabilityCacheModel,
    AvailabilityStatisticsModel
)
from app.data.models.supplier_model import ProductSupplierLink
from app.data.models.dataset_model import (
    DatasetModel,
    DatasetTagModel,
    DatasetVersionModel,
    DatasetStatisticsModel,
    DatasetImageModel,
    DatasetVideoModel,
    DatasetMetadataModel,
)
from app.data.models.annotation_model import (
    AnnotationModel,
    AnnotationObjectModel,
    AnnotationLabelModel,
    AnnotationReviewModel,
    AnnotationVersionModel,
    AnnotationHistoryModel,
    AnnotationCommentModel,
    AnnotationTaskModel,
)
from app.data.models.preprocessing_model import (
    PreprocessingJobModel,
    PreprocessingLogModel,
    ImageQualityModel,
    VideoProcessingModel,
    PipelineConfigurationModel,
)
from app.data.models.validation_model import (
    ValidationJobModel,
    DatasetQualityReportModel,
    ValidationErrorModel,
    QualityScoreModel,
    ClassDistributionModel,
    ReviewHistoryModel,
    DatasetApprovalModel,
)
from app.data.models.model_registry_model import (
    AIModelModel,
    AIModelVersionModel,
    ModelArtifactModel,
    ModelMetricModel,
    ModelDeploymentModel,
    DeploymentHistoryModel,
    ModelReviewModel,
    ModelTagModel,
    ModelPermissionModel,
)

# AI inference models
from app.ai_inference.models import (
    InferenceJobModel,
    InferenceResultModel,
    DetectionModel,
    ProcessedImageModel,
    ProcessedVideoModel,
    RuntimeStatisticModel,
)

# Barcode models
from app.barcode.models import (
    BarcodeTypeModel,
    BarcodeScanModel,
    BarcodeResultModel,
    UnknownBarcodeModel,
    BarcodeQualityModel,
)

# Product recognition models
from app.product_recognition.models import (
    ProductMatchModel,
    MatchCandidateModel,
    MatchScoreModel,
    RecognitionHistoryModel,
    UnknownProductModel,
    RecognitionFeedbackModel,
)

# Auto-create tables for foundation demo/test runs
try:
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize database schemas: {str(e)}")

# Create FastAPI instance
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for the AI-Powered Grocery Inventory System.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Custom & Core Middlewares (SOLID, Clean Architecture Layers)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TracingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local storage folder if provider is set to local
if settings.STORAGE_PROVIDER == "local":
    os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
    app.mount("/static/uploads", StaticFiles(directory=settings.LOCAL_STORAGE_DIR), name="static")
    logger.info(f"Local storage mounted at /static/uploads -> {settings.LOCAL_STORAGE_DIR}")

# Error handling
register_exception_handlers(app)

# Include APIs
app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    """Initializes database tables and verifies schema migration state on launch."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema sync completed successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables on startup: {e}")


# --- API FOUNDATION ENDPOINTS (Phase 3 Specifications) ---

def check_db_health() -> bool:
    """Verifies relational database socket accessibility."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False


@app.get("/health", tags=["system-foundation"])
def health_check(response: Response):
    """System health check verifying database pool connectivity."""
    db_ok = check_db_health()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "app": settings.APP_NAME,
            "environment": settings.APP_ENV
        }
    return {
        "status": "healthy",
        "database": "connected",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV
    }


@app.get("/ready", tags=["system-foundation"])
def readiness_check(response: Response):
    """Signals Kubernetes uvicorn container is ready to route traffic."""
    db_ok = check_db_health()
    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}
    return {"status": "ready"}


@app.get("/live", tags=["system-foundation"])
def liveness_check():
    """Signals Kubernetes container process is alive."""
    return {"status": "live"}


@app.get("/version", tags=["system-foundation"])
def version_check():
    """System version and environment diagnostic information."""
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.APP_ENV,
        "debug_mode": settings.DEBUG
    }


@app.get("/metrics", tags=["system-foundation"])
def metrics_exporter():
    """Exposes system metrics in plain text format for Prometheus scraping."""
    import sys
    import gc
    
    # Generate basic metric counters
    object_count = len(gc.get_objects())
    metrics_payload = (
        "# HELP python_info Python platform info\n"
        "# TYPE python_info gauge\n"
        f'python_info{{version="{sys.version.split()[0]}"}} 1.0\n'
        "# HELP app_objects_total Total python objects active\n"
        "# TYPE app_objects_total gauge\n"
        f"app_objects_total {object_count}\n"
    )
    return Response(content=metrics_payload, media_type="text/plain")


@app.get("/", tags=["system-foundation"])
def index():
    return {
        "message": f"Welcome to the {settings.APP_NAME} foundation.",
        "documentation": "/docs"
    }
