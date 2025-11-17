"""
API v1 Router - aggregates all API routes
"""
from fastapi import APIRouter
from app.api.v1 import citations, search, import_routes, bulk_import, treatment, admin, opinions, citation_sync

api_router = APIRouter()

# Include route modules
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(citations.router, prefix="/citations", tags=["citations"])
api_router.include_router(treatment.router, prefix="/treatment", tags=["treatment"])
api_router.include_router(import_routes.router, prefix="/import", tags=["import"])
api_router.include_router(bulk_import.router, prefix="/bulk", tags=["bulk-import"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(opinions.router, prefix="/opinions", tags=["opinions"])
api_router.include_router(citation_sync.router, prefix="/citation-sync", tags=["citation-sync"])

