import json
import redis.asyncio as aioredis

_redis: aioredis.Redis | None = None


async def init_redis(redis_url: str):
    global _redis
    _redis = aioredis.from_url(redis_url, decode_responses=True)
    await _redis.ping()


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


def get_redis() -> aioredis.Redis:
    assert _redis is not None, "Redis not initialized"
    return _redis


# ---- Pipeline Status (replaces in-memory pipeline_status dict) ----

PIPELINE_STATUS_KEY = "pipeline:status"
PIPELINE_PROGRESS_KEY = "pipeline:progress"


async def set_pipeline_status(running: bool, last_result: dict | None = None):
    r = get_redis()
    mapping = {"running": "1" if running else "0"}
    if last_result is not None:
        mapping["last_result"] = json.dumps(last_result, ensure_ascii=False)
    await r.hset(PIPELINE_STATUS_KEY, mapping=mapping)
    await r.expire(PIPELINE_STATUS_KEY, 86400)


async def get_pipeline_status() -> dict:
    r = get_redis()
    data = await r.hgetall(PIPELINE_STATUS_KEY)
    if not data:
        return {"running": False, "last_result": None}
    last_result = None
    if data.get("last_result"):
        try:
            last_result = json.loads(data["last_result"])
        except (json.JSONDecodeError, TypeError):
            pass
    return {
        "running": data.get("running") == "1",
        "last_result": last_result,
    }


# ---- Pipeline Progress (replaces in-memory PipelineProgress) ----

async def set_pipeline_progress(percentage: int, step: str, message: str):
    r = get_redis()
    await r.hset(PIPELINE_PROGRESS_KEY, mapping={
        "percentage": str(percentage),
        "step": step,
        "message": message,
    })
    await r.expire(PIPELINE_PROGRESS_KEY, 86400)


async def get_pipeline_progress() -> dict:
    r = get_redis()
    data = await r.hgetall(PIPELINE_PROGRESS_KEY)
    if not data:
        return {"percentage": 0, "step": "idle", "message": "等待中"}
    return {
        "percentage": int(data.get("percentage", 0)),
        "step": data.get("step", "idle"),
        "message": data.get("message", "等待中"),
    }


# ---- User Trigger Count (replaces in-memory user_trigger_count) ----

async def get_user_trigger_count(user_id: int) -> tuple[str, int]:
    r = get_redis()
    key = f"trigger:{user_id}"
    data = await r.hgetall(key)
    return data.get("date", ""), int(data.get("count", 0))


async def increment_user_trigger(user_id: int, today: str):
    r = get_redis()
    key = f"trigger:{user_id}"
    current_date = await r.hget(key, "date")
    if current_date != today:
        await r.hset(key, mapping={"date": today, "count": "1"})
    else:
        await r.hincrby(key, "count", 1)
    await r.expire(key, 86400 * 2)


# ---- Report Cache ----

async def cache_report(report_id: int, data: dict, ttl: int = 86400):
    r = get_redis()
    await r.set(f"report:{report_id}", json.dumps(data, ensure_ascii=False), ex=ttl)


async def get_cached_report(report_id: int) -> dict | None:
    r = get_redis()
    val = await r.get(f"report:{report_id}")
    return json.loads(val) if val else None


async def invalidate_report_cache(report_id: int = None):
    """Invalidate specific report or latest report cache."""
    r = get_redis()
    if report_id:
        await r.delete(f"report:{report_id}")
    await r.delete("report:latest")
