from datetime import date, datetime

from sqlalchemy import ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Batch(Base):
    __tablename__ = 'batches'

    id: Mapped[int] = mapped_column(primary_key=True)

    # Статус
    is_closed: Mapped[bool] = mapped_column(default=False)
    closed_at: Mapped[datetime | None]

    # Описание задания
    task_description: Mapped[str]
    work_center_id: Mapped[int] = mapped_column(ForeignKey('work_centers.id'))
    shift: Mapped[str]
    team: Mapped[str]

    # Идентификация партии
    batch_number: Mapped[int] = mapped_column(index=True)
    batch_date: Mapped[date] = mapped_column(index=True)

    # Продукция
    nomenclature: Mapped[str]
    ekn_code: Mapped[str]

    # Временные рамки
    shift_start: Mapped[datetime]
    shift_end: Mapped[datetime]

    # Метаданные
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Связи
    products: Mapped[list['Product']] = relationship(back_populates='batch', lazy='selectin') #type: ignore
    work_center: Mapped['WorkCenter'] = relationship(back_populates='batches')  #type: ignore

    __table_args__ = (
        UniqueConstraint('batch_number', 'batch_date', name='uq_batch_number_date'),
        Index('idx_batch_closed', 'is_closed'),
        Index('idx_batch_shift_times', 'shift_start', 'shift_end'),
    )
