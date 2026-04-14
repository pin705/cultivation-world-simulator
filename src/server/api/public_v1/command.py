from __future__ import annotations

from typing import Callable, Literal, Optional

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from src.config import RunConfig
from src.server.services.public_api_contract import ok_response


class GameStartRequest(RunConfig):
    pass


class SetObjectiveRequest(BaseModel):
    avatar_id: str
    content: str
    viewer_id: Optional[str] = None


class ClearObjectiveRequest(BaseModel):
    avatar_id: str
    viewer_id: Optional[str] = None


class GrantAvatarSupportRequest(BaseModel):
    avatar_id: str
    viewer_id: Optional[str] = None


class AppointAvatarSeedRequest(BaseModel):
    avatar_id: str
    viewer_id: Optional[str] = None


class ClaimSectRequest(BaseModel):
    sect_id: int
    viewer_id: Optional[str] = None


class SetMainAvatarRequest(BaseModel):
    avatar_id: str
    viewer_id: Optional[str] = None


class ChoosePlayerOpeningRequest(BaseModel):
    choice_id: str
    viewer_id: Optional[str] = None


class SwitchControlSeatRequest(BaseModel):
    controller_id: str
    viewer_id: Optional[str] = None


class ReleaseControlSeatRequest(BaseModel):
    controller_id: str
    viewer_id: Optional[str] = None


class UpdatePlayerProfileRequest(BaseModel):
    viewer_id: Optional[str] = None
    display_name: str


class TransferPlayerIdentityRequest(BaseModel):
    source_viewer_id: str
    preferred_display_name: Optional[str] = None
    viewer_id: Optional[str] = None


class SwitchWorldRoomRequest(BaseModel):
    room_id: str
    viewer_id: Optional[str] = None


class UpdateWorldRoomAccessRequest(BaseModel):
    room_id: str
    access_mode: Literal["open", "private"]
    viewer_id: Optional[str] = None


class UpdateWorldRoomPlanRequest(BaseModel):
    room_id: str
    plan_id: str
    viewer_id: Optional[str] = None


class UpdateWorldRoomEntitlementRequest(BaseModel):
    room_id: str
    billing_status: Literal["trial", "active", "grace", "expired"]
    entitled_plan_id: str
    viewer_id: Optional[str] = None


class CreateWorldRoomPaymentOrderRequest(BaseModel):
    room_id: str
    target_plan_id: str
    viewer_id: Optional[str] = None


class SettleWorldRoomPaymentRequest(BaseModel):
    room_id: str
    order_id: str
    payment_ref: Optional[str] = None
    amount_vnd: Optional[int] = None
    viewer_id: Optional[str] = None


class SePayWorldRoomWebhookRequest(BaseModel):
    id: Optional[str | int] = None
    gateway: Optional[str] = None
    transaction_id: Optional[str] = None
    transaction_date: Optional[str] = None
    transactionDate: Optional[str] = None
    reference_code: Optional[str] = None
    referenceCode: Optional[str] = None
    transfer_type: Optional[str] = None
    transferType: Optional[str] = None
    amount: Optional[int | float | str] = None
    transferAmount: Optional[int | float | str] = None
    content: Optional[str] = None
    description: Optional[str] = None


class ReconcileWorldRoomPaymentRequest(BaseModel):
    viewer_id: Optional[str] = None
    transfer_note: str
    amount_vnd: Optional[int] = None
    payment_ref: Optional[str] = None


class UpdateWorldRoomMemberRequest(BaseModel):
    room_id: str
    member_viewer_id: str
    viewer_id: Optional[str] = None


class RotateWorldRoomInviteRequest(BaseModel):
    room_id: str
    viewer_id: Optional[str] = None


class JoinWorldRoomByInviteRequest(BaseModel):
    room_id: str
    invite_code: str
    viewer_id: Optional[str] = None


class SetSectDirectiveRequest(BaseModel):
    sect_id: int
    content: str
    viewer_id: Optional[str] = None


class ClearSectDirectiveRequest(BaseModel):
    sect_id: int
    viewer_id: Optional[str] = None


class InterveneSectRelationRequest(BaseModel):
    sect_id: int
    other_sect_id: int
    mode: Literal["ease", "escalate"]
    viewer_id: Optional[str] = None


class CreateAvatarRequest(BaseModel):
    surname: Optional[str] = None
    given_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    level: Optional[int] = None
    sect_id: Optional[int] = None
    persona_ids: Optional[list[int]] = None
    pic_id: Optional[int] = None
    technique_id: Optional[int] = None
    weapon_id: Optional[int] = None
    auxiliary_id: Optional[int] = None
    alignment: Optional[str] = None
    appearance: Optional[int] = None
    relations: Optional[list[dict]] = None


class DeleteAvatarRequest(BaseModel):
    avatar_id: str


class UpdateAvatarAdjustmentRequest(BaseModel):
    avatar_id: str
    category: Literal["technique", "weapon", "auxiliary", "personas", "goldfinger"]
    target_id: Optional[int] = None
    persona_ids: Optional[list[int]] = None


class UpdateAvatarPortraitRequest(BaseModel):
    avatar_id: str
    pic_id: int


class GenerateCustomContentRequest(BaseModel):
    category: Literal["technique", "weapon", "auxiliary", "goldfinger"]
    realm: Optional[str] = None
    user_prompt: str


class CreateCustomContentRequest(BaseModel):
    category: Literal["technique", "weapon", "auxiliary", "goldfinger"]
    draft: dict


class SetPhenomenonRequest(BaseModel):
    id: int


class SaveGameRequest(BaseModel):
    custom_name: Optional[str] = None


class DeleteSaveRequest(BaseModel):
    filename: str


class LoadGameRequest(BaseModel):
    filename: str


class AcknowledgeRecapRequest(BaseModel):
    viewer_id: Optional[str] = None


class SpendActionPointRequest(BaseModel):
    viewer_id: Optional[str] = None


class FundDiscipleRequest(BaseModel):
    funding_type: str = "pills"  # pills/manuals/weapons/closed_door
    viewer_id: Optional[str] = None


class SetSectPriorityRequest(BaseModel):
    priority: str = "cultivation"  # cultivation/expansion/diplomacy/commerce/defense
    viewer_id: Optional[str] = None


def create_public_command_router(
    *,
    run_start_game: Callable[[BaseModel], object],
    run_reinit_game: Callable[[], object],
    run_reset_game: Callable[[], object],
    trigger_process_shutdown: Callable[[], dict],
    run_pause_game: Callable[[], object],
    run_resume_game: Callable[[], object],
    run_set_long_term_objective: Callable[[BaseModel], object],
    run_clear_long_term_objective: Callable[[BaseModel], object],
    run_grant_avatar_support: Callable[[BaseModel], object],
    run_appoint_avatar_seed: Callable[[BaseModel], object],
    run_claim_sect: Callable[[BaseModel], object],
    run_set_main_avatar: Callable[[BaseModel], object],
    run_choose_player_opening: Callable[[BaseModel], object],
    run_switch_control_seat: Callable[[BaseModel], object],
    run_release_control_seat: Callable[[BaseModel], object],
    run_update_player_profile: Callable[[BaseModel], object],
    run_transfer_player_identity: Callable[[BaseModel], object],
    run_switch_world_room: Callable[[BaseModel], object],
    run_update_world_room_access: Callable[[BaseModel], object],
    run_update_world_room_plan: Callable[[BaseModel], object],
    run_update_world_room_entitlement: Callable[[BaseModel], object],
    run_create_world_room_payment_order: Callable[[BaseModel], object],
    run_settle_world_room_payment: Callable[[BaseModel], object],
    run_receive_sepay_world_room_payment_webhook: Callable[..., object],
    run_reconcile_world_room_payment: Callable[[BaseModel], object],
    run_add_world_room_member: Callable[[BaseModel], object],
    run_remove_world_room_member: Callable[[BaseModel], object],
    run_rotate_world_room_invite: Callable[[BaseModel], object],
    run_join_world_room_by_invite: Callable[[BaseModel], object],
    run_set_sect_directive: Callable[[BaseModel], object],
    run_clear_sect_directive: Callable[[BaseModel], object],
    run_intervene_sect_relation: Callable[[BaseModel], object],
    run_create_avatar: Callable[[BaseModel], object],
    run_delete_avatar: Callable[..., object],
    run_update_avatar_adjustment: Callable[[BaseModel], object],
    run_update_avatar_portrait: Callable[..., object],
    run_generate_custom_content: Callable[[BaseModel], object],
    run_create_custom_content: Callable[[BaseModel], object],
    run_set_phenomenon: Callable[..., object],
    run_cleanup_events: Callable[..., object],
    run_save_game: Callable[..., dict],
    run_delete_save: Callable[..., dict],
    run_load_game: Callable[..., object],
    run_acknowledge_recap: Callable[[BaseModel], object],  # NEW: recap acknowledgment
    run_spend_action_point: Callable[[BaseModel], object],  # NEW: action point spending
    run_fund_disciple: Callable[[BaseModel], object],  # NEW: disciple funding
    run_set_sect_priority: Callable[[BaseModel], object],  # NEW: sect priority
    resolve_viewer_id: Callable[[Request, str | None], str | None] | None = None,
) -> APIRouter:
    router = APIRouter()

    def _resolve_request_viewer_id(request: Request, viewer_id: str | None) -> str | None:
        if callable(resolve_viewer_id):
            return resolve_viewer_id(request, viewer_id)
        normalized = str(viewer_id or "").strip()
        return normalized or None

    def _copy_request_with_viewer_id(req: BaseModel, viewer_id: str | None) -> BaseModel:
        if hasattr(req, "model_copy"):
            return req.model_copy(update={"viewer_id": viewer_id})
        payload = req.dict()
        payload["viewer_id"] = viewer_id
        return req.__class__(**payload)

    @router.post("/api/v1/command/game/start")
    async def start_game_v1(req: GameStartRequest):
        return ok_response(await run_start_game(req))

    @router.post("/api/v1/command/game/reinit")
    async def reinit_game_v1():
        return ok_response(await run_reinit_game())

    @router.post("/api/v1/command/game/reset")
    async def reset_game_v1():
        return ok_response(await run_reset_game())

    @router.post("/api/v1/command/system/shutdown")
    async def shutdown_server_v1():
        return ok_response(trigger_process_shutdown())

    @router.post("/api/v1/command/game/pause")
    async def pause_game_v1():
        return ok_response(await run_pause_game())

    @router.post("/api/v1/command/game/resume")
    async def resume_game_v1():
        return ok_response(await run_resume_game())

    @router.post("/api/v1/command/avatar/set-long-term-objective")
    async def set_long_term_objective_v1(request: Request, req: SetObjectiveRequest):
        return ok_response(
            await run_set_long_term_objective(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/avatar/clear-long-term-objective")
    async def clear_long_term_objective_v1(request: Request, req: ClearObjectiveRequest):
        return ok_response(
            await run_clear_long_term_objective(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/avatar/grant-support")
    async def grant_avatar_support_v1(request: Request, req: GrantAvatarSupportRequest):
        return ok_response(
            await run_grant_avatar_support(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/avatar/appoint-seed")
    async def appoint_avatar_seed_v1(request: Request, req: AppointAvatarSeedRequest):
        return ok_response(
            await run_appoint_avatar_seed(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/player/claim-sect")
    async def claim_sect_v1(request: Request, req: ClaimSectRequest):
        return ok_response(
            await run_claim_sect(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/player/set-main-avatar")
    async def set_main_avatar_v1(request: Request, req: SetMainAvatarRequest):
        return ok_response(
            await run_set_main_avatar(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/player/choose-opening")
    async def choose_player_opening_v1(request: Request, req: ChoosePlayerOpeningRequest):
        return ok_response(
            await run_choose_player_opening(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/player/switch-seat")
    async def switch_control_seat_v1(request: Request, req: SwitchControlSeatRequest):
        return ok_response(
            await run_switch_control_seat(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/player/release-seat")
    async def release_control_seat_v1(request: Request, req: ReleaseControlSeatRequest):
        return ok_response(
            await run_release_control_seat(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/player/update-profile")
    async def update_player_profile_v1(request: Request, req: UpdatePlayerProfileRequest):
        return ok_response(
            await run_update_player_profile(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/player/transfer-identity")
    async def transfer_player_identity_v1(request: Request, req: TransferPlayerIdentityRequest):
        return ok_response(
            await run_transfer_player_identity(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/switch")
    async def switch_world_room_v1(request: Request, req: SwitchWorldRoomRequest):
        return ok_response(
            await run_switch_world_room(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/update-access")
    async def update_world_room_access_v1(request: Request, req: UpdateWorldRoomAccessRequest):
        return ok_response(
            await run_update_world_room_access(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/update-plan")
    async def update_world_room_plan_v1(request: Request, req: UpdateWorldRoomPlanRequest):
        return ok_response(
            await run_update_world_room_plan(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/update-entitlement")
    async def update_world_room_entitlement_v1(request: Request, req: UpdateWorldRoomEntitlementRequest):
        return ok_response(
            await run_update_world_room_entitlement(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/create-payment-order")
    async def create_world_room_payment_order_v1(request: Request, req: CreateWorldRoomPaymentOrderRequest):
        return ok_response(
            await run_create_world_room_payment_order(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/settle-payment")
    async def settle_world_room_payment_v1(request: Request, req: SettleWorldRoomPaymentRequest):
        return ok_response(
            await run_settle_world_room_payment(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/webhooks/sepay/world-room-payment")
    async def sepay_world_room_payment_webhook_v1(
        req: SePayWorldRoomWebhookRequest,
        x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ):
        payload = req.model_dump() if hasattr(req, "model_dump") else req.dict()
        return ok_response(
            await run_receive_sepay_world_room_payment_webhook(
                payload=payload,
                provided_api_key=x_api_key,
                provided_authorization=authorization,
            )
        )

    @router.post("/api/v1/command/world-room/reconcile-payment")
    async def reconcile_world_room_payment_v1(request: Request, req: ReconcileWorldRoomPaymentRequest):
        return ok_response(
            await run_reconcile_world_room_payment(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/add-member")
    async def add_world_room_member_v1(request: Request, req: UpdateWorldRoomMemberRequest):
        return ok_response(
            await run_add_world_room_member(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/remove-member")
    async def remove_world_room_member_v1(request: Request, req: UpdateWorldRoomMemberRequest):
        return ok_response(
            await run_remove_world_room_member(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/rotate-invite")
    async def rotate_world_room_invite_v1(request: Request, req: RotateWorldRoomInviteRequest):
        return ok_response(
            await run_rotate_world_room_invite(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/world-room/join-by-invite")
    async def join_world_room_by_invite_v1(request: Request, req: JoinWorldRoomByInviteRequest):
        return ok_response(
            await run_join_world_room_by_invite(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/sect/set-directive")
    async def set_sect_directive_v1(request: Request, req: SetSectDirectiveRequest):
        return ok_response(
            await run_set_sect_directive(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/sect/clear-directive")
    async def clear_sect_directive_v1(request: Request, req: ClearSectDirectiveRequest):
        return ok_response(
            await run_clear_sect_directive(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/sect/intervene-relation")
    async def intervene_sect_relation_v1(request: Request, req: InterveneSectRelationRequest):
        return ok_response(
            await run_intervene_sect_relation(
                _copy_request_with_viewer_id(req, _resolve_request_viewer_id(request, req.viewer_id))
            )
        )

    @router.post("/api/v1/command/avatar/create")
    async def create_avatar_v1(req: CreateAvatarRequest):
        return ok_response(await run_create_avatar(req))

    @router.post("/api/v1/command/avatar/delete")
    async def delete_avatar_v1(req: DeleteAvatarRequest):
        return ok_response(await run_delete_avatar(avatar_id=req.avatar_id))

    @router.post("/api/v1/command/avatar/update-adjustment")
    async def update_avatar_adjustment_v1(req: UpdateAvatarAdjustmentRequest):
        return ok_response(await run_update_avatar_adjustment(req))

    @router.post("/api/v1/command/avatar/update-portrait")
    async def update_avatar_portrait_v1(req: UpdateAvatarPortraitRequest):
        return ok_response(
            await run_update_avatar_portrait(avatar_id=req.avatar_id, pic_id=req.pic_id)
        )

    @router.post("/api/v1/command/avatar/generate-custom-content")
    async def generate_custom_content_v1(req: GenerateCustomContentRequest):
        return ok_response(await run_generate_custom_content(req))

    @router.post("/api/v1/command/avatar/create-custom-content")
    def create_custom_content_v1(req: CreateCustomContentRequest):
        return ok_response(run_create_custom_content(req))

    @router.post("/api/v1/command/world/set-phenomenon")
    async def set_phenomenon_v1(req: SetPhenomenonRequest):
        return ok_response(await run_set_phenomenon(phenomenon_id=req.id))

    @router.delete("/api/v1/command/events/cleanup")
    async def cleanup_events_v1(
        keep_major: bool = True,
        before_month_stamp: int = None,
    ):
        return ok_response(
            await run_cleanup_events(
                keep_major=keep_major,
                before_month_stamp=before_month_stamp,
            )
        )

    @router.post("/api/v1/command/game/save")
    def api_save_game_v1(req: SaveGameRequest):
        return ok_response(run_save_game(custom_name=req.custom_name))

    @router.post("/api/v1/command/game/delete-save")
    def api_delete_game_v1(req: DeleteSaveRequest):
        return ok_response(run_delete_save(filename=req.filename))

    @router.post("/api/v1/command/game/load")
    async def api_load_game_v1(req: LoadGameRequest):
        return ok_response(await run_load_game(filename=req.filename))

    # NEW: Recap command endpoints
    @router.post("/api/v1/command/recap/acknowledge")
    async def acknowledge_recap_v1(request: Request, req: AcknowledgeRecapRequest):
        resolved_viewer_id = _resolve_request_viewer_id(request, req.viewer_id)
        if not resolved_viewer_id:
            return ok_response({"error": "viewer_id is required"})
        payload = req.model_copy(update={"viewer_id": resolved_viewer_id})
        return ok_response(await run_acknowledge_recap(payload))

    @router.post("/api/v1/command/recap/spend-action-point")
    async def spend_action_point_v1(request: Request, req: SpendActionPointRequest):
        resolved_viewer_id = _resolve_request_viewer_id(request, req.viewer_id)
        if not resolved_viewer_id:
            return ok_response({"error": "viewer_id is required"})
        payload = req.model_copy(update={"viewer_id": resolved_viewer_id})
        return ok_response(await run_spend_action_point(payload))

    # NEW: Disciple funding endpoint
    @router.post("/api/v1/command/disciple/fund")
    async def fund_disciple_v1(request: Request, req: FundDiscipleRequest):
        resolved_viewer_id = _resolve_request_viewer_id(request, req.viewer_id)
        if not resolved_viewer_id:
            return ok_response({"error": "viewer_id is required"})
        payload = req.model_copy(update={"viewer_id": resolved_viewer_id})
        return ok_response(await run_fund_disciple(payload))

    # NEW: Sect priority endpoint
    @router.post("/api/v1/command/sect/set-priority")
    async def set_sect_priority_v1(request: Request, req: SetSectPriorityRequest):
        resolved_viewer_id = _resolve_request_viewer_id(request, req.viewer_id)
        if not resolved_viewer_id:
            return ok_response({"error": "viewer_id is required"})
        payload = req.model_copy(update={"viewer_id": resolved_viewer_id})
        return ok_response(await run_set_sect_priority(payload))

    return router
