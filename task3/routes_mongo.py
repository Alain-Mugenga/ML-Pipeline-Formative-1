from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, Response
from pymongo.errors import DuplicateKeyError

from database import mongo_readings
from models import Reading, ReadingCreate

router = APIRouter(prefix="/mongo", tags=["MongoDB"])


def to_naive_utc(moment: datetime) -> datetime:
    """MongoDB stores dates in UTC. Turn an aware datetime into naive UTC
    so it compares the same way as in MySQL."""
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment


def doc_to_reading(doc: dict) -> dict:
    """Turn a MongoDB document into the API's shape (_id -> id as a string)."""
    return {
        "id": str(doc["_id"]),
        "recorded_at": doc["recorded_at"],
        "global_active_power": float(doc["global_active_power"]),
        "global_reactive_power": float(doc["global_reactive_power"]),
        "voltage": float(doc["voltage"]),
        "global_intensity": float(doc["global_intensity"]),
        "submeters": {
            "sub_metering_1": float(doc["submeters"]["sub_metering_1"]),
            "sub_metering_2": float(doc["submeters"]["sub_metering_2"]),
            "sub_metering_3": float(doc["submeters"]["sub_metering_3"]),
        },
    }


def reading_to_doc(reading: ReadingCreate) -> dict:
    """The document to store: the request body as-is, with recorded_at in UTC."""
    doc = reading.model_dump()
    doc["recorded_at"] = to_naive_utc(reading.recorded_at)
    return doc


def parse_id(reading_id: str) -> ObjectId:
    """Turn the id from the URL into an ObjectId, or 404 if it isn't one."""
    if not ObjectId.is_valid(reading_id):
        raise HTTPException(status_code=404, detail="Reading not found")
    return ObjectId(reading_id)


# --- Time-series endpoints (fixed paths: keep these above /readings/{reading_id}) ---


@router.get("/readings/latest", response_model=Reading)
def get_latest_reading():
    """The most recent reading, by recorded_at."""
    doc = mongo_readings.find_one(sort=[("recorded_at", -1)])
    if doc is None:
        raise HTTPException(status_code=404, detail="No readings found")
    return doc_to_reading(doc)


@router.get("/readings/range", response_model=list[Reading])
def get_readings_by_date_range(
    start: datetime,
    end: datetime,
    limit: int = Query(1000, ge=1, le=10000),
):
    """Readings with start <= recorded_at <= end, oldest first."""
    start, end = to_naive_utc(start), to_naive_utc(end)
    if start > end:
        raise HTTPException(status_code=400, detail="start must be before end")

    cursor = (
        mongo_readings.find({"recorded_at": {"$gte": start, "$lte": end}})
        .sort("recorded_at", 1)
        .limit(limit)
    )
    return [doc_to_reading(doc) for doc in cursor]


# --- CRUD endpoints ---


@router.get("/readings", response_model=list[Reading])
def list_readings(
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    """A page of readings, oldest first."""
    cursor = mongo_readings.find().sort("recorded_at", 1).skip(offset).limit(limit)
    return [doc_to_reading(doc) for doc in cursor]


@router.get("/readings/{reading_id}", response_model=Reading)
def get_reading(reading_id: str):
    """One reading by its id."""
    doc = mongo_readings.find_one({"_id": parse_id(reading_id)})
    if doc is None:
        raise HTTPException(status_code=404, detail="Reading not found")
    return doc_to_reading(doc)


@router.post("/readings", response_model=Reading, status_code=201)
def create_reading(reading: ReadingCreate):
    """Create a reading: one document, submeters nested inside it."""
    doc = reading_to_doc(reading)
    try:
        result = mongo_readings.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="A reading with this recorded_at already exists",
        )
    doc["_id"] = result.inserted_id
    return doc_to_reading(doc)


@router.put("/readings/{reading_id}", response_model=Reading)
def update_reading(reading_id: str, reading: ReadingCreate):
    """Replace a reading completely (same body as POST)."""
    oid = parse_id(reading_id)
    doc = reading_to_doc(reading)
    try:
        result = mongo_readings.replace_one({"_id": oid}, doc)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail="Another reading already has this recorded_at",
        )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Reading not found")
    doc["_id"] = oid
    return doc_to_reading(doc)


@router.delete("/readings/{reading_id}", status_code=204)
def delete_reading(reading_id: str):
    """Delete a reading. Its submeters are inside the document, so they go too."""
    result = mongo_readings.delete_one({"_id": parse_id(reading_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Reading not found")
    return Response(status_code=204)