from fastapi import APIRouter

# Import all endpoint routers
from api.endpoints import users, companies, accounts, backup, builds, packages, reports, computers, licenses, administrators

# Create the main API router
router = APIRouter()

# Include all endpoint routers with proper tags
router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

router.include_router(
    companies.router,
    prefix="/companies",
    tags=["Companies"]
)

router.include_router(
    accounts.router,
    prefix="/accounts",
    tags=["Accounts"]
)

router.include_router(
    backup.router,
    prefix="/backup",
    tags=["Backup"]
)

router.include_router(
    builds.router,
    prefix="/builds",
    tags=["Builds"]
)

router.include_router(
    packages.router,
    prefix="/packages",
    tags=["Packages"]
)

router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"]
)

router.include_router(
    computers.router,
    prefix="/computers",
    tags=["Computers"]
)

router.include_router(
    licenses.router,
    prefix="/licenses",
    tags=["Licenses"]
)

router.include_router(
    administrators.router,
    prefix="/administrators",
    tags=["Administrators"]
) 