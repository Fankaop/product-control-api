from datetime import datetime

from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)

    unique_code: Mapped[str] = mapped_column(unique=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey('batches.id'), index=True)

    # Аггрегация
    is_aggregated: Mapped[bool] = mapped_column(default=False, index=True)
    aggregated_at: Mapped[datetime | None]

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Связи
    batch: Mapped['Batch'] = relationship(back_populates='products')  #type: ignore

    __table_args__ = (
        Index('idx_product_batch_aggregated', 'batch_id', 'is_aggregated'),
    )
