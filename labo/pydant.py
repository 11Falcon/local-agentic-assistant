from pydantic import BaseModel

class Model(BaseModel):
    a: int
    b:float
    c: str

print(Model(a= 2.000, b='2.22', c = b'binary data').model_dump())


from datetime import datetime, timezone, timedelta
def find_free_slots(busy, day_start, day_end, duration_minutes):
    # sorting the busy
    busy = sorted(busy, key=lambda x : datetime.fromisoformat(x["start"]))
    cursor = datetime.fromisoformat(day_start)
    end_limit = datetime.fromisoformat(day_end)
    need = timedelta(minutes=duration_minutes)
    out = []
    for event in busy:
        block_start = datetime.fromisoformat(event["start"])
        block_end = datetime.fromisoformat(event["end"])
        if block_start - cursor >= need:
            out.append({'start' : cursor.isoformat(), 'end' : block_start.isoformat()})
        cursor = max(cursor, block_end)
    if end_limit - cursor >= need:
        out.append({"start" : cursor.isoformat(), "end" : end_limit.isoformat()})
    return out