from datetime import date, datetime, time
from math import ceil
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from database import get_db
from router.auth import get_current_user
from models import Category, Complaint, StatusHistory
from schemas import CategoryOut, ComplaintCreate, ComplaintOut, ComplaintUpdate, PaginatedComplaints

router = APIRouter(tags=['Complaints'])
Db = Depends(get_db)


def complaint_response(complaint: Complaint, db: Session) -> ComplaintOut:
	history = db.query(StatusHistory).filter(StatusHistory.complaint_id == complaint.id).order_by(StatusHistory.created_at.asc()).all()
	return ComplaintOut(
		id=complaint.id,
		title=complaint.title,
		description=complaint.description,
		location=complaint.location,
		image_url=complaint.image_url,
		priority=complaint.priority,
		status=complaint.status,
		reporter_id=complaint.reporter_id,
		category_id=complaint.category_id,
		assigned_to_id=complaint.assigned_to_id,
		resolution_note=complaint.resolution_note,
		created_at=complaint.created_at,
		updated_at=complaint.updated_at,
		history=history,
	)


@router.get('/categories', response_model=list[CategoryOut])
def categories(db: Session = Db):
	return db.query(Category).filter(Category.is_active == True).order_by(Category.name).all()


def listing(db, user_id=None, search=None, category_id=None, status=None, date_from=None, date_to=None, sort='newest', page=1, page_size=10):
	query = db.query(Complaint)
	if user_id is not None:
		query = query.filter(Complaint.reporter_id == user_id)
	if search:
		query = query.filter(or_(Complaint.title.ilike(f'%{search}%'), Complaint.description.ilike(f'%{search}%'), Complaint.location.ilike(f'%{search}%')))
	if category_id:
		query = query.filter(Complaint.category_id == category_id)
	if status:
		query = query.filter(Complaint.status == status)
	if date_from:
		query = query.filter(Complaint.created_at >= datetime.combine(date_from, time.min))
	if date_to:
		query = query.filter(Complaint.created_at <= datetime.combine(date_to, time.max))
	query = query.order_by(Complaint.title.asc() if sort == 'alphabetical' else Complaint.created_at.asc() if sort == 'oldest' else Complaint.created_at.desc())
	total = query.count()
	items = query.offset((page - 1) * page_size).limit(page_size).all()
	return PaginatedComplaints(items=[complaint_response(item, db) for item in items], total=total, page=page, page_size=page_size, total_pages=ceil(total / page_size) if total else 0)


@router.get('/complaints/my', response_model=PaginatedComplaints)
def my_complaints(user=Depends(get_current_user), db: Session = Db, search: Optional[str] = None, category_id: Optional[int] = None, status: Optional[str] = None, date_from: Optional[date] = None, date_to: Optional[date] = None, sort: str = Query('newest', pattern='^(newest|oldest|alphabetical)$'), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50)):
	return listing(db, user['id'], search, category_id, status, date_from, date_to, sort, page, page_size)


@router.post('/complaints', response_model=ComplaintOut, status_code=201)
def create_complaint(data: ComplaintCreate, user=Depends(get_current_user), db: Session = Db):
	if not db.query(Category).filter(Category.id == data.category_id, Category.is_active == True).first():
		raise HTTPException(400, 'Category not found')
	complaint = Complaint(**data.model_dump(), reporter_id=user['id'])
	db.add(complaint)
	db.flush()
	db.add(StatusHistory(complaint_id=complaint.id, status='pending', note='Complaint submitted', changed_by_id=user['id']))
	db.commit()
	db.refresh(complaint)
	return complaint_response(complaint, db)


@router.get('/complaints/{complaint_id}', response_model=ComplaintOut)
def get_complaint(complaint_id: int, user=Depends(get_current_user), db: Session = Db):
	complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
	if not complaint:
		raise HTTPException(404, 'Complaint not found')
	if complaint.reporter_id != user['id'] and user['role'] != 'admin':
		raise HTTPException(403, 'You cannot access this complaint')
	return complaint_response(complaint, db)


@router.put('/complaints/{complaint_id}', response_model=ComplaintOut)
def update_complaint(complaint_id: int, data: ComplaintUpdate, user=Depends(get_current_user), db: Session = Db):
	complaint = db.query(Complaint).filter(Complaint.id == complaint_id, Complaint.reporter_id == user['id']).first()
	if not complaint:
		raise HTTPException(404, 'Complaint not found')
	if complaint.status != 'pending':
		raise HTTPException(400, 'Only pending complaints can be edited')
	for key, value in data.model_dump(exclude_unset=True).items():
		setattr(complaint, key, value)
	db.commit()
	db.refresh(complaint)
	return complaint_response(complaint, db)


@router.delete('/complaints/{complaint_id}')
def delete_complaint(complaint_id: int, user=Depends(get_current_user), db: Session = Db):
	complaint = db.query(Complaint).filter(Complaint.id == complaint_id, Complaint.reporter_id == user['id']).first()
	if not complaint:
		raise HTTPException(404, 'Complaint not found')
	if complaint.status != 'pending':
		raise HTTPException(400, 'Only pending complaints can be deleted')
	db.query(StatusHistory).filter(StatusHistory.complaint_id == complaint.id).delete(synchronize_session=False)
	db.delete(complaint)
	db.commit()
	return {'message': 'Complaint deleted successfully'}
