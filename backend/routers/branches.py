"""Branch management routes"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from database import db
from models import BranchCreate, BranchResponse, Branch, UserRole
from auth import (
    get_current_user, require_role,
    get_tenant_filter, add_tenant_id, log_audit
)

router = APIRouter(prefix="/branches", tags=["Branches"])


@router.post("", response_model=BranchResponse)
async def create_branch(branch_data: BranchCreate, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Create a new branch"""
    branch = Branch(**branch_data.model_dump())
    doc = branch.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc = add_tenant_id(doc, current_user)
    await db.branches.insert_one(doc)
    await log_audit(current_user["id"], "create_branch", "branch", branch.id)
    return BranchResponse(**doc)


@router.get("", response_model=List[BranchResponse])
async def get_branches(current_user: dict = Depends(get_current_user)):
    """Get all branches"""
    tenant_filter = get_tenant_filter(current_user)
    branches = await db.branches.find(tenant_filter, {"_id": 0}).to_list(1000)
    return [BranchResponse(**b) for b in branches]


@router.get("/{branch_id}", response_model=BranchResponse)
async def get_branch(branch_id: str, current_user: dict = Depends(get_current_user)):
    """Get a branch by ID"""
    tenant_filter = get_tenant_filter(current_user)
    branch = await db.branches.find_one({"id": branch_id, **tenant_filter}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Dega nuk u gjet")
    return BranchResponse(**branch)


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: str,
    branch_data: BranchCreate,
    current_user: dict = Depends(require_role([UserRole.ADMIN]))
):
    """Update a branch"""
    tenant_filter = get_tenant_filter(current_user)
    update_dict = branch_data.model_dump()
    await db.branches.update_one({"id": branch_id, **tenant_filter}, {"$set": update_dict})
    branch = await db.branches.find_one({"id": branch_id, **tenant_filter}, {"_id": 0})
    if not branch:
        raise HTTPException(status_code=404, detail="Dega nuk u gjet")
    await log_audit(current_user["id"], "update_branch", "branch", branch_id)
    return BranchResponse(**branch)


@router.delete("/{branch_id}")
async def delete_branch(branch_id: str, current_user: dict = Depends(require_role([UserRole.ADMIN]))):
    """Delete a branch"""
    tenant_filter = get_tenant_filter(current_user)
    result = await db.branches.delete_one({"id": branch_id, **tenant_filter})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Dega nuk u gjet")
    await log_audit(current_user["id"], "delete_branch", "branch", branch_id)
    return {"message": "Dega u fshi me sukses"}
