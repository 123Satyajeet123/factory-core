from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel


class Cadence(BaseModel):
    workflow: str
    crontab: str
    last: datetime | None = None
    allowed: bool = False

    def trigger(self):
        from apscheduler.triggers.cron import CronTrigger

        return CronTrigger.from_crontab(self.crontab, timezone="UTC")

    def next_after(self, moment: datetime | None = None) -> datetime | None:
        previous = self.last
        return self.trigger().get_next_fire_time(previous, moment or previous or _now())


def _now() -> datetime:
    return datetime.now(UTC)


def owed(cadence: Cadence, now: datetime | None = None) -> int:
    now = now or _now()
    if cadence.last is None:
        return 1 if cadence.next_after(now) and cadence.next_after(now) <= now else 0
    trigger, at, count = cadence.trigger(), cadence.last, 0
    while count < 1000:
        at = trigger.get_next_fire_time(at, at)
        if at is None or at > now:
            return count
        count += 1
    return count


def due(cadence: Cadence, now: datetime | None = None) -> bool:
    return cadence.allowed and owed(cadence, now) > 0


def _self_check() -> None:
    """uv run python -m factory.orchestrate.schedule"""
    from datetime import timedelta

    nine = Cadence(workflow="outreach", crontab="0 9 * * *", allowed=True)
    monday = datetime(2026, 8, 31, 8, 0, tzinfo=UTC)

    assert not due(nine, monday), "an hour early is not due"
    ran = nine.model_copy(update={"last": monday.replace(hour=9)})
    assert not due(ran, monday.replace(hour=10)), "already ran today"
    assert due(ran, monday + timedelta(days=1, hours=1)), "tomorrow it is due again"

    asleep = ran.model_copy(update={"last": monday.replace(hour=9)})
    woke = monday + timedelta(days=6, hours=1)
    assert owed(asleep, woke) == 6, owed(asleep, woke)

    refused = ran.model_copy(update={"allowed": False})
    assert not due(refused, monday + timedelta(days=1, hours=1)), \
        "nothing runs unattended before somebody allowed it"
    assert owed(refused, monday + timedelta(days=1, hours=1)) == 1, \
        "owed still counts; allowed is a separate answer"

    print(f"schedule: six days asleep owes {owed(asleep, woke)} runs, "
          f"and owes them whether or not it is allowed to make them")


if __name__ == "__main__":
    _self_check()
