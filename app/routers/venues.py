from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Venue, User
from app import auth, schemas

router = APIRouter(prefix="/venues", tags=["venues"])

@router.post("", response_model=schemas.VenueOut, status_code=201)
def create_venue(body: schemas.VenueCreate, db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    venue = Venue(**body.model_dump(), organizer_id=user.id)
    db.add(venue); db.commit(); db.refresh(venue)
    return venue

@router.get("", response_model=list[schemas.VenueOut])
def list_venues(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Venue).offset(skip).limit(limit).all()

@router.get("/mine", response_model=list[schemas.VenueOut])
def my_venues(db: Session = Depends(get_db),
              user: User = Depends(auth.require_role("organizer"))):
    return db.query(Venue).filter_by(organizer_id=user.id).all()

@router.get("/{venue_id}", response_model=schemas.VenueOut)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    v = db.get(Venue, venue_id)
    if not v: raise HTTPException(404, "Venue not found")
    return v

@router.put("/{venue_id}", response_model=schemas.VenueOut)
def update_venue(venue_id: int, body: schemas.VenueUpdate,
                 db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    v = db.get(Venue, venue_id)
    if not v: raise HTTPException(404, "Venue not found")
    if v.organizer_id != user.id: raise HTTPException(403, "Not your venue")
    for k, val in body.model_dump(exclude_unset=True).items():
        setattr(v, k, val)
    db.commit(); db.refresh(v)
    return v

@router.delete("/{venue_id}", status_code=204)
def delete_venue(venue_id: int, db: Session = Depends(get_db),
                 user: User = Depends(auth.require_role("organizer"))):
    v = db.get(Venue, venue_id)
    if not v: raise HTTPException(404, "Venue not found")
    if v.organizer_id != user.id: raise HTTPException(403, "Not your venue")
    db.delete(v); db.commit()
