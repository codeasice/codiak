from fastapi import APIRouter
from api.routers.dragon_keeper.sync import router as sync_router
from api.routers.dragon_keeper.safe_to_spend import router as sts_router
from api.routers.dragon_keeper.account_summary import router as account_router
from api.routers.dragon_keeper.sync_health import router as health_router
from api.routers.dragon_keeper.categorization import router as categorization_router
from api.routers.dragon_keeper.write_back import router as write_back_router
from api.routers.dragon_keeper.learning import router as learning_router
from api.routers.dragon_keeper.spending_trends import router as trends_router
from api.routers.dragon_keeper.engagement import router as engagement_router
from api.routers.dragon_keeper.dragon_state import router as dragon_state_router
from api.routers.dragon_keeper.category_detail import router as category_detail_router
from api.routers.dragon_keeper.rules_management import router as rules_mgmt_router
from api.routers.dragon_keeper.rule_preview import router as rule_preview_router
from api.routers.dragon_keeper.keeper_chat import router as keeper_chat_router
from api.routers.dragon_keeper.transaction_explorer import router as txn_explorer_router
from api.routers.dragon_keeper.recurring import router as recurring_router
from api.routers.dragon_keeper.dk_settings import router as dk_settings_router
from api.routers.dragon_keeper.paycheck_tracer import router as paycheck_tracer_router

router = APIRouter()

router.include_router(sync_router)
router.include_router(sts_router)
router.include_router(account_router)
router.include_router(health_router)
router.include_router(categorization_router)
router.include_router(write_back_router)
router.include_router(learning_router)
router.include_router(trends_router)
router.include_router(engagement_router)
router.include_router(dragon_state_router)
router.include_router(category_detail_router)
router.include_router(rules_mgmt_router)
router.include_router(rule_preview_router)
router.include_router(keeper_chat_router)
router.include_router(txn_explorer_router)
router.include_router(recurring_router)
router.include_router(dk_settings_router)
router.include_router(paycheck_tracer_router)


@router.get("/health")
def dragon_keeper_health():
    return {"status": "ok", "module": "dragon-keeper"}
