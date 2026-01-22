from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    Call,
    CallStatus,
    Insight,
    InsightType,
    Transcript,
)


# Call CRUD

class CRUDCall:
    """CRUD operations for Call model."""

    async def create(
        self,
        session: AsyncSession,
        *,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
    ) -> Call:
        """Create a new call record."""
        call = Call(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            status=CallStatus.UPLOADED,
        )
        session.add(call)
        await session.commit()
        await session.refresh(call)
        return call

    async def get(self, session: AsyncSession, *, id: int) -> Call | None:
        """Get a call by ID."""
        return await session.get(Call, id)

    async def get_with_details(
        self, session: AsyncSession, *, id: int
    ) -> Call | None:
        """Get a call with its transcripts and insights eagerly loaded."""
        query = (
            select(Call)
            .where(Call.id == id)
            .options(
                selectinload(Call.transcripts),
                selectinload(Call.insights),
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        session: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 20,
        status: CallStatus | None = None,
    ) -> list[Call]:
        """Get multiple calls with optional status filter."""
        query = select(Call)

        if status is not None:
            query = query.where(Call.status == status)

        query = query.order_by(Call.created_at.desc()).offset(skip).limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        session: AsyncSession,
        *,
        status: CallStatus | None = None,
    ) -> int:
        """Count calls with optional status filter."""
        query = select(func.count(Call.id))

        if status is not None:
            query = query.where(Call.status == status)

        result = await session.execute(query)
        return result.scalar_one()

    async def update_status(
        self,
        session: AsyncSession,
        *,
        call: Call,
        status: CallStatus,
        error_message: str | None = None,
        duration_seconds: float | None = None,
    ) -> Call:
        """Update call status and related fields."""
        call.status = status
        call.updated_at = datetime.utcnow()

        if error_message is not None:
            call.error_message = error_message

        if duration_seconds is not None:
            call.duration_seconds = duration_seconds

        session.add(call)
        await session.commit()
        await session.refresh(call)
        return call

    async def delete(self, session: AsyncSession, *, id: int) -> bool:
        """Delete a call and its related data (cascade)."""
        call = await session.get(Call, id)
        if call is None:
            return False

        await session.delete(call)
        await session.commit()
        return True


# Transcript CRUD

class CRUDTranscript:
    """CRUD operations for Transcript model."""

    async def create(
        self,
        session: AsyncSession,
        *,
        call_id: int,
        speaker: str,
        text: str,
        start_time: int,
        end_time: int,
        confidence: float | None = None,
    ) -> Transcript:
        """Create a single transcript utterance."""
        transcript = Transcript(
            call_id=call_id,
            speaker=speaker,
            text=text,
            start_time=start_time,
            end_time=end_time,
            confidence=confidence,
        )
        session.add(transcript)
        await session.commit()
        await session.refresh(transcript)
        return transcript

    async def create_many(
        self,
        session: AsyncSession,
        *,
        call_id: int,
        utterances: list[dict],
    ) -> list[Transcript]:
        """
        Bulk create transcript utterances.

        utterances should be a list of dicts with keys:
        speaker, text, start_time, end_time, confidence (optional)
        """
        transcripts = [
            Transcript(call_id=call_id, **utterance) for utterance in utterances
        ]
        session.add_all(transcripts)
        await session.commit()

        # Refresh all to get IDs
        for t in transcripts:
            await session.refresh(t)

        return transcripts

    async def get_by_call(
        self,
        session: AsyncSession,
        *,
        call_id: int,
    ) -> list[Transcript]:
        """Get all transcripts for a call, ordered by start time."""
        query = (
            select(Transcript)
            .where(Transcript.call_id == call_id)
            .order_by(Transcript.start_time)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_full_text(
        self,
        session: AsyncSession,
        *,
        call_id: int,
    ) -> str:
        """Get the full transcript as a single string with speaker labels."""
        transcripts = await self.get_by_call(session, call_id=call_id)
        lines = [f"{t.speaker}: {t.text}" for t in transcripts]
        return "\n".join(lines)


# Insight CRUD

class CRUDInsight:
    """CRUD operations for Insight model."""

    async def create(
        self,
        session: AsyncSession,
        *,
        call_id: int,
        insight_type: InsightType,
        content: str,
        confidence: float | None = None,
        extra_data: dict | None = None,
    ) -> Insight:
        """Create a single insight."""
        insight = Insight(
            call_id=call_id,
            insight_type=insight_type,
            content=content,
            confidence=confidence,
            extra_data=extra_data or {},
        )
        session.add(insight)
        await session.commit()
        await session.refresh(insight)
        return insight

    async def create_many(
        self,
        session: AsyncSession,
        *,
        call_id: int,
        insights: list[dict],
    ) -> list[Insight]:
        """
        Bulk create insights.

        insights should be a list of dicts with keys:
        insight_type, content, confidence (optional), metadata (optional)
        """
        insight_objs = [Insight(call_id=call_id, **ins) for ins in insights]
        session.add_all(insight_objs)
        await session.commit()

        for i in insight_objs:
            await session.refresh(i)

        return insight_objs

    async def get_by_call(
        self,
        session: AsyncSession,
        *,
        call_id: int,
        insight_type: InsightType | None = None,
    ) -> list[Insight]:
        """Get insights for a call, optionally filtered by type."""
        query = select(Insight).where(Insight.call_id == call_id)

        if insight_type is not None:
            query = query.where(Insight.insight_type == insight_type)

        query = query.order_by(Insight.created_at)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        session: AsyncSession,
        *,
        insight_type: InsightType,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Insight]:
        """Get all insights of a specific type across all calls."""
        query = (
            select(Insight)
            .where(Insight.insight_type == insight_type)
            .order_by(Insight.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

# Singleton instances

call_crud = CRUDCall()
transcript_crud = CRUDTranscript()
insight_crud = CRUDInsight()
