from datetime import datetime, date, timedelta, timezone

from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.batch import Batch
from data.models.product import Product
from data.models.work_center import WorkCenter


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_dashboard_stats(self) -> dict:
        today = date.today()

        # Summary
        total_batches = await self.session.scalar(select(func.count(Batch.id))) or 0
        open_batches = await self.session.scalar(
            select(func.count(Batch.id)).where(Batch.is_closed == False)
        ) or 0
        total_products = await self.session.scalar(select(func.count(Product.id))) or 0
        aggregated_products = await self.session.scalar(
            select(func.count(Product.id)).where(Product.is_aggregated == True)
        ) or 0

        # Today
        batches_created_today = await self.session.scalar(
            select(func.count(Batch.id)).where(func.date(Batch.created_at) == today)
        ) or 0
        batches_closed_today = await self.session.scalar(
            select(func.count(Batch.id)).where(func.date(Batch.closed_at) == today)
        ) or 0
        products_added_today = await self.session.scalar(
            select(func.count(Product.id)).where(func.date(Product.created_at) == today)
        ) or 0
        products_aggregated_today = await self.session.scalar(
            select(func.count(Product.id)).where(func.date(Product.aggregated_at) == today)
        ) or 0

        # By shift
        shifts_result = await self.session.execute(
            select(
                Batch.shift,
                func.count(func.distinct(Batch.id)).label("batches"),
                func.count(Product.id).label("products"),
                func.sum(Product.is_aggregated.cast(Integer)).label("aggregated"),
            )
            .outerjoin(Product, Product.batch_id == Batch.id)
            .group_by(Batch.shift)
        )
        by_shift = {
            row.shift: {
                "batches": row.batches,
                "products": row.products or 0,
                "aggregated": int(row.aggregated or 0),
            }
            for row in shifts_result
        }

        # Top work centers
        top_wc_result = await self.session.execute(
            select(
                WorkCenter.id,
                WorkCenter.name,
                WorkCenter.identifier,
                func.count(func.distinct(Batch.id)).label("batches_count"),
                func.count(Product.id).label("products_count"),
                func.sum(Product.is_aggregated.cast(Integer)).label("aggregated"),
            )
            .join(Batch, Batch.work_center_id == WorkCenter.id)
            .outerjoin(Product, Product.batch_id == Batch.id)
            .group_by(WorkCenter.id, WorkCenter.name, WorkCenter.identifier)
            .order_by(func.count(Batch.id).desc())
            .limit(5)
        )
        top_work_centers = []
        for row in top_wc_result:
            products = row.products_count or 0
            aggregated = int(row.aggregated or 0)
            top_work_centers.append({
                "id": row.id,
                "identifier": row.identifier,
                "name": row.name,
                "batches_count": row.batches_count,
                "products_count": products,
                "aggregation_rate": round(aggregated / products * 100, 1) if products > 0 else 0.0,
            })

        return {
            "summary": {
                "total_batches": total_batches,
                "active_batches": open_batches,
                "closed_batches": total_batches - open_batches,
                "total_products": total_products,
                "aggregated_products": aggregated_products,
                "aggregation_rate": round(aggregated_products / total_products * 100, 1) if total_products > 0 else 0.0,
            },
            "today": {
                "batches_created": batches_created_today,
                "batches_closed": batches_closed_today,
                "products_added": products_added_today,
                "products_aggregated": products_aggregated_today,
            },
            "by_shift": by_shift,
            "top_work_centers": top_work_centers,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_batch_stats(self, batch_id: int) -> dict:
        batch = await self.session.get(Batch, batch_id)
        if batch is None:
            return {}

        total = await self.session.scalar(
            select(func.count(Product.id)).where(Product.batch_id == batch_id)
        ) or 0
        aggregated = await self.session.scalar(
            select(func.count(Product.id)).where(
                Product.batch_id == batch_id,
                Product.is_aggregated == True,
            )
        ) or 0

        # Timeline
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        shift_duration = (batch.shift_end - batch.shift_start).total_seconds() / 3600
        elapsed = min((now - batch.shift_start).total_seconds() / 3600, shift_duration)
        products_per_hour = round(aggregated / elapsed, 2) if elapsed > 0 else 0.0

        remaining = total - aggregated
        estimated_completion = None
        if products_per_hour > 0 and remaining > 0:
            hours_left = remaining / products_per_hour
            estimated_completion = (now + timedelta(hours=hours_left)).isoformat()

        return {
            "batch_info": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "batch_date": str(batch.batch_date),
                "is_closed": batch.is_closed,
            },
            "production_stats": {
                "total_products": total,
                "aggregated": aggregated,
                "remaining": remaining,
                "aggregation_rate": round(aggregated / total * 100, 1) if total > 0 else 0.0,
            },
            "timeline": {
                "shift_duration_hours": round(shift_duration, 2),
                "elapsed_hours": round(elapsed, 2),
                "products_per_hour": products_per_hour,
                "estimated_completion": estimated_completion,
            },
            "team_performance": {
                "team": batch.team,
                "avg_products_per_hour": products_per_hour,
            },
        }

    async def get_work_center_stats(self, work_center_id: int) -> dict:
        total_batches = await self.session.scalar(
            select(func.count(Batch.id)).where(Batch.work_center_id == work_center_id)
        ) or 0
        closed_batches = await self.session.scalar(
            select(func.count(Batch.id)).where(
                Batch.work_center_id == work_center_id,
                Batch.is_closed == True,
            )
        ) or 0
        total_products = await self.session.scalar(
            select(func.count(Product.id)).join(Batch).where(Batch.work_center_id == work_center_id)
        ) or 0

        return {
            "work_center_id": work_center_id,
            "total_batches": total_batches,
            "closed_batches": closed_batches,
            "open_batches": total_batches - closed_batches,
            "total_products": total_products,
        }

    async def compare_batches(self, batch_ids: list[int]) -> dict:
        rows = await self.session.execute(
            select(
                Batch.id,
                Batch.batch_number,
                Batch.shift_start,
                Batch.shift_end,
                func.count(Product.id).label("total"),
                func.sum(Product.is_aggregated.cast(Integer)).label("aggregated"),
            )
            .outerjoin(Product, Product.batch_id == Batch.id)
            .where(Batch.id.in_(batch_ids))
            .group_by(Batch.id, Batch.batch_number, Batch.shift_start, Batch.shift_end)
        )

        comparison = []
        for row in rows:
            total = row.total or 0
            aggregated = int(row.aggregated or 0)
            duration = (row.shift_end - row.shift_start).total_seconds() / 3600
            comparison.append({
                "batch_id": row.id,
                "batch_number": row.batch_number,
                "total_products": total,
                "aggregated": aggregated,
                "rate": round(aggregated / total * 100, 1) if total > 0 else 0.0,
                "duration_hours": round(duration, 2),
                "products_per_hour": round(aggregated / duration, 2) if duration > 0 else 0.0,
            })

        avg_rate = round(sum(b["rate"] for b in comparison) / len(comparison), 2) if comparison else 0.0
        avg_pph = round(sum(b["products_per_hour"] for b in comparison) / len(comparison), 2) if comparison else 0.0

        return {
            "comparison": comparison,
            "average": {
                "aggregation_rate": avg_rate,
                "products_per_hour": avg_pph,
            },
        }
