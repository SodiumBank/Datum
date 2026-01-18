from fastapi import FastAPI
from services.api.routers import auth, health, uploads, quotes, rules, plans, tests, revisions, soe, outputs, compliance, profiles

app = FastAPI(title="Datum API", version="0.1.0")

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
app.include_router(quotes.router, prefix="/quotes", tags=["quotes"])
app.include_router(rules.router, prefix="/rules", tags=["rules"])
app.include_router(plans.router, prefix="/plans", tags=["plans"])
app.include_router(tests.router, prefix="/tests", tags=["tests"])
app.include_router(revisions.router, prefix="/revisions", tags=["revisions"])
app.include_router(soe.router, prefix="/soe", tags=["soe"])
app.include_router(outputs.router, prefix="/outputs", tags=["outputs"])
app.include_router(compliance.router, prefix="/compliance", tags=["compliance"])

app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
