from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ReferenceImageModel(Base):
    """Reference images for product verification using visual embeddings."""
    __tablename__ = "reference_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Image storage
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Image metadata
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Embedding data (JSON string of numpy array)
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Quality metrics
    quality_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    
    # Processing status
    embedding_generated: Mapped[bool] = mapped_column(default=False, nullable=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product: Mapped["ProductModel"] = relationship(
        "ProductModel",
        back_populates="reference_images"
    )
