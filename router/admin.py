from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from router.auth import get_current_user
from models import Category, Complaint, StatusHistory, User
from schemas import AdminComplaintUpdate, CategoryCreate, CategoryOut, ComplaintOut, PaginatedComplaints, UserOut
from router.complaints import complaint_response, listing

router = APIRouter(prefix='/admin', tags=['Administration'])
Db = Depends(get_db)


def admin_user(user=Depends(get_current_user)):
	if user['role'] != 'admin':
		raise HTTPException(403, 'Admin access required')
	return user


@router.get('/dashboard')
def dashboard(_: dict = Depends(admin_user), db: Session = Db):
	counts = {status: db.query(Complaint).filter(Complaint.status == status).count() for status in ['pending', 'in_progress', 'resolved', 'rejected']}
	return {'total': sum(counts.values()), **counts}


@router.get('/complaints', response_model=PaginatedComplaints)
def all_complaints(_: dict = Depends(admin_user), db: Session = Db, search: Optional[str] = None, category_id: Optional[int] = None, status: Optional[str] = None, sort: str = Query('newest', pattern='^(newest|oldest|alphabetical)$'), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50)):
	return listing(db, None, search, category_id, status, None, None, sort, page, page_size)


@router.put('/complaints/{complaint_id}', response_model=ComplaintOut)
def update_admin_complaint(complaint_id: int, data: AdminComplaintUpdate, admin: dict = Depends(admin_user), db: Session = Db):
	complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
	if not complaint:
		raise HTTPException(404, 'Complaint not found')
	values = data.model_dump(exclude_unset=True)
	if 'assigned_to_id' in values and values['assigned_to_id'] is not None and not db.query(User).filter(User.id == values['assigned_to_id'], User.is_active == True).first():
		raise HTTPException(400, 'Active assignee not found')
	old_status = complaint.status
	for key, value in values.items():
		setattr(complaint, key, value)
	if 'status' in values and values['status'] != old_status:
		db.add(StatusHistory(complaint_id=complaint.id, status=values['status'], note=values.get('resolution_note') or '', changed_by_id=admin['id']))
	db.commit()
	db.refresh(complaint)
	return complaint_response(complaint, db)


@router.post('/categories', response_model=CategoryOut, status_code=201)
def create_category(data: CategoryCreate, _: dict = Depends(admin_user), db: Session = Db):
	if db.query(Category).filter(func.lower(Category.name) == data.name.lower()).first():
		raise HTTPException(400, 'Category already exists')
	category = Category(**data.model_dump())
	db.add(category)
	db.commit()
	db.refresh(category)
	return category


@router.put('/categories/{category_id}', response_model=CategoryOut)
def update_category(category_id: int, data: CategoryCreate, _: dict = Depends(admin_user), db: Session = Db):
	category = db.query(Category).filter(Category.id == category_id).first()
	if not category:
		raise HTTPException(404, 'Category not found')
	category.name, category.description = data.name, data.description
	db.commit()
	db.refresh(category)
	return category


@router.delete('/categories/{category_id}')
def delete_category(category_id: int, _: dict = Depends(admin_user), db: Session = Db):
	category = db.query(Category).filter(Category.id == category_id).first()
	if not category:
		raise HTTPException(404, 'Category not found')
	category.is_active = False
	db.commit()
	return {'message': 'Category deactivated'}


@router.get('/users', response_model=list[UserOut])
def users(_: dict = Depends(admin_user), db: Session = Db):
	return db.query(User).order_by(User.created_at.desc()).all()


@router.patch('/users/{user_id}/toggle')
def toggle_user(user_id: int, admin: dict = Depends(admin_user), db: Session = Db):
	user = db.query(User).filter(User.id == user_id).first()
	if not user:
		raise HTTPException(404, 'User not found')
	if user.id == admin['id']:
		raise HTTPException(400, 'You cannot deactivate yourself')
	user.is_active = not user.is_active
	db.commit()
	return {'is_active': user.is_active}
