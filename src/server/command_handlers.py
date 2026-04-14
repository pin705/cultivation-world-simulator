from __future__ import annotations

from types import SimpleNamespace

from src.config import RunConfig, get_settings_service
from src.i18n import t
from src.server.services.player_control import (
    claim_player_sect,
    release_player_control_seat,
    set_player_main_avatar,
    switch_player_control_seat,
    update_player_profile,
)
from src.server.services.world_room_control import (
    add_world_room_member,
    create_world_room_payment_order,
    join_world_room_by_invite,
    reconcile_world_room_payment,
    receive_sepay_world_room_payment_webhook,
    remove_world_room_member,
    rotate_world_room_invite,
    settle_world_room_payment,
    switch_active_world_room,
    update_world_room_access,
    update_world_room_entitlement,
    update_world_room_plan,
)


def create_command_handlers(
    *,
    get_runtime,
    room_registry,
    get_player_auth_store,
    manager,
    avatar_assets,
    assets_path: str,
    model_to_dict,
    validate_save_name,
    get_init_game_async,
    get_apply_runtime_content_locale,
    scan_avatar_assets,
    start_game_lifecycle,
    reinit_game_lifecycle,
    cleanup_events_command,
    set_world_phenomenon,
    celestial_phenomena_by_id,
    create_avatar_in_world,
    create_avatar_from_request,
    sects_by_id,
    uses_space_separated_names,
    language_manager,
    alignment_from_str,
    get_appearance_by_level,
    delete_avatar_in_world,
    update_avatar_adjustment_in_world,
    apply_avatar_adjustment,
    update_avatar_portrait_in_world,
    generate_custom_content_command,
    get_generate_custom_goldfinger_draft,
    get_generate_custom_content_draft,
    realm_from_str,
    create_custom_content_command,
    create_custom_goldfinger_from_draft,
    create_custom_content_from_draft,
    set_long_term_objective_for_avatar,
    clear_long_term_objective_for_avatar,
    set_user_long_term_objective,
    clear_user_long_term_objective,
    grant_player_support_for_avatar,
    appoint_player_seed_for_avatar,
    set_player_directive_for_sect,
    clear_player_directive_for_sect,
    intervene_relation_for_sects,
    save_current_game,
    save_game,
    delete_save_file,
    get_config,
    get_fallback_saves_dirs,
    get_load_game_into_runtime,
    get_load_game,
    get_events_db_path,
):
    def _runtime():
        return get_runtime()

    def _persist_runtime_player_state(target_runtime) -> None:
        if room_registry is None:
            return
        room_id = getattr(room_registry, "get_room_id_for_runtime", lambda _runtime: None)(target_runtime)
        if room_id is None:
            room_id = getattr(room_registry, "get_active_room_id", lambda: "main")()
        capturer = getattr(room_registry, "capture_runtime_player_state", None)
        if callable(capturer):
            capturer(room_id)

    async def run_start_game(req) -> dict:
        runtime = _runtime()
        run_config = RunConfig(**model_to_dict(req))
        return await start_game_lifecycle(
            runtime,
            run_config=run_config,
            apply_runtime_content_locale=get_apply_runtime_content_locale(),
            init_game_async=get_init_game_async(runtime),
        )

    async def run_reinit_game() -> dict:
        runtime = _runtime()
        return await reinit_game_lifecycle(runtime, init_game_async=get_init_game_async(runtime))

    async def run_reset_game() -> dict:
        runtime = _runtime()
        await runtime.run_mutation(runtime.reset_to_idle)
        return {"status": "ok", "message": "Game reset to idle"}

    async def run_pause_game() -> dict:
        runtime = _runtime()
        await runtime.run_mutation(runtime.set_paused, True)
        return {"status": "ok", "message": "Game paused"}

    async def run_resume_game() -> dict:
        runtime = _runtime()
        await runtime.run_mutation(runtime.set_paused, False)
        return {"status": "ok", "message": "Game resumed"}

    async def run_cleanup_events(*, keep_major: bool, before_month_stamp: int | None) -> dict:
        runtime = _runtime()
        return await runtime.run_mutation(
            cleanup_events_command,
            runtime,
            keep_major=keep_major,
            before_month_stamp=before_month_stamp,
        )

    async def run_set_phenomenon(*, phenomenon_id: int) -> dict:
        runtime = _runtime()
        return await runtime.run_mutation(
            set_world_phenomenon,
            runtime,
            phenomenon_id=phenomenon_id,
            celestial_phenomena_by_id=celestial_phenomena_by_id,
        )

    async def run_create_avatar(req) -> dict:
        runtime = _runtime()
        return await runtime.run_mutation(
            create_avatar_in_world,
            runtime,
            req=req,
            create_avatar_from_request=create_avatar_from_request,
            sects_by_id=sects_by_id,
            uses_space_separated_names=uses_space_separated_names,
            language_manager=language_manager,
            avatar_assets=avatar_assets,
            alignment_from_str=alignment_from_str,
            get_appearance_by_level=get_appearance_by_level,
        )

    async def run_delete_avatar(*, avatar_id: str) -> dict:
        runtime = _runtime()
        return await runtime.run_mutation(
            delete_avatar_in_world,
            runtime,
            avatar_id=avatar_id,
        )

    async def run_update_avatar_adjustment(req) -> dict:
        runtime = _runtime()
        return await runtime.run_mutation(
            update_avatar_adjustment_in_world,
            runtime,
            avatar_id=req.avatar_id,
            category=req.category,
            target_id=req.target_id,
            persona_ids=req.persona_ids,
            apply_avatar_adjustment=apply_avatar_adjustment,
        )

    async def run_update_avatar_portrait(*, avatar_id: str, pic_id: int) -> dict:
        runtime = _runtime()
        return await runtime.run_mutation(
            update_avatar_portrait_in_world,
            runtime,
            avatar_id=avatar_id,
            pic_id=pic_id,
            avatar_assets=avatar_assets,
        )

    async def run_generate_custom_content(req) -> dict:
        return await generate_custom_content_command(
            category=req.category,
            realm=req.realm,
            user_prompt=req.user_prompt,
            generate_custom_goldfinger_draft=get_generate_custom_goldfinger_draft(),
            generate_custom_content_draft=get_generate_custom_content_draft(),
            realm_from_str=realm_from_str,
        )

    def run_create_custom_content(req) -> dict:
        return create_custom_content_command(
            category=req.category,
            draft=req.draft,
            create_custom_goldfinger_from_draft=create_custom_goldfinger_from_draft,
            create_custom_content_from_draft=create_custom_content_from_draft,
        )

    async def run_set_long_term_objective(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            set_long_term_objective_for_avatar,
            runtime,
            avatar_id=req.avatar_id,
            content=req.content,
            setter=set_user_long_term_objective,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_clear_long_term_objective(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            clear_long_term_objective_for_avatar,
            runtime,
            avatar_id=req.avatar_id,
            clearer=clear_user_long_term_objective,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_grant_avatar_support(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            grant_player_support_for_avatar,
            runtime,
            avatar_id=req.avatar_id,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_appoint_avatar_seed(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            appoint_player_seed_for_avatar,
            runtime,
            avatar_id=req.avatar_id,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_claim_sect(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            claim_player_sect,
            runtime,
            sect_id=req.sect_id,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_set_main_avatar(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            set_player_main_avatar,
            runtime,
            avatar_id=req.avatar_id,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_switch_control_seat(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            switch_player_control_seat,
            runtime,
            controller_id=req.controller_id,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_release_control_seat(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            release_player_control_seat,
            runtime,
            controller_id=req.controller_id,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_update_player_profile(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            update_player_profile,
            runtime,
            viewer_id=req.viewer_id,
            display_name=req.display_name,
        )
        _persist_runtime_player_state(runtime)
        auth_store = get_player_auth_store()
        if auth_store is not None and getattr(req, "viewer_id", None):
            auth_store.update_player_display_name(req.viewer_id, req.display_name)
        return result

    async def run_switch_world_room(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            switch_active_world_room,
            room_registry=room_registry,
            room_id=req.room_id,
            viewer_id=getattr(req, "viewer_id", None),
        )

    async def run_update_world_room_access(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            update_world_room_access,
            room_registry=room_registry,
            room_id=req.room_id,
            access_mode=req.access_mode,
            viewer_id=req.viewer_id,
        )

    async def run_update_world_room_plan(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            update_world_room_plan,
            room_registry=room_registry,
            room_id=req.room_id,
            plan_id=req.plan_id,
            viewer_id=req.viewer_id,
        )

    async def run_update_world_room_entitlement(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            update_world_room_entitlement,
            room_registry=room_registry,
            room_id=req.room_id,
            billing_status=req.billing_status,
            entitled_plan_id=req.entitled_plan_id,
            viewer_id=req.viewer_id,
        )

    async def run_create_world_room_payment_order(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            create_world_room_payment_order,
            room_registry=room_registry,
            room_id=req.room_id,
            target_plan_id=req.target_plan_id,
            viewer_id=req.viewer_id,
        )

    async def run_settle_world_room_payment(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            settle_world_room_payment,
            room_registry=room_registry,
            room_id=req.room_id,
            order_id=req.order_id,
            viewer_id=req.viewer_id,
            payment_ref=getattr(req, "payment_ref", None),
            amount_vnd=getattr(req, "amount_vnd", None),
        )

    async def run_receive_sepay_world_room_payment_webhook(
        *,
        payload: dict,
        provided_api_key: str | None = None,
        provided_authorization: str | None = None,
    ) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            receive_sepay_world_room_payment_webhook,
            room_registry=room_registry,
            payload=payload,
            provided_api_key=provided_api_key,
            provided_authorization=provided_authorization,
        )

    async def run_reconcile_world_room_payment(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            reconcile_world_room_payment,
            room_registry=room_registry,
            viewer_id=req.viewer_id,
            transfer_note=req.transfer_note,
            amount_vnd=getattr(req, "amount_vnd", None),
            payment_ref=getattr(req, "payment_ref", None),
        )

    async def run_add_world_room_member(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            add_world_room_member,
            room_registry=room_registry,
            room_id=req.room_id,
            member_viewer_id=req.member_viewer_id,
            viewer_id=req.viewer_id,
        )

    async def run_remove_world_room_member(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            remove_world_room_member,
            room_registry=room_registry,
            room_id=req.room_id,
            member_viewer_id=req.member_viewer_id,
            viewer_id=req.viewer_id,
        )

    async def run_rotate_world_room_invite(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            rotate_world_room_invite,
            room_registry=room_registry,
            room_id=req.room_id,
            viewer_id=req.viewer_id,
        )

    async def run_join_world_room_by_invite(req) -> dict:
        current_runtime = _runtime()
        return await current_runtime.run_mutation(
            join_world_room_by_invite,
            room_registry=room_registry,
            room_id=req.room_id,
            invite_code=req.invite_code,
            viewer_id=req.viewer_id,
        )

    async def run_set_sect_directive(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            set_player_directive_for_sect,
            runtime,
            sect_id=req.sect_id,
            content=req.content,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_clear_sect_directive(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            clear_player_directive_for_sect,
            runtime,
            sect_id=req.sect_id,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    async def run_intervene_sect_relation(req) -> dict:
        runtime = _runtime()
        result = await runtime.run_mutation(
            intervene_relation_for_sects,
            runtime,
            sect_id=req.sect_id,
            other_sect_id=req.other_sect_id,
            mode=req.mode,
            viewer_id=req.viewer_id,
        )
        _persist_runtime_player_state(runtime)
        return result

    def run_save_game(*, custom_name: str | None) -> dict:
        runtime = _runtime()
        return save_current_game(
            runtime,
            custom_name=custom_name,
            validate_save_name=validate_save_name,
            save_game=save_game,
            sects_by_id=sects_by_id,
            room_registry=room_registry,
        )

    def run_delete_save(*, filename: str) -> dict:
        return delete_save_file(
            filename=filename,
            saves_dir=get_config().paths.saves,
            fallback_saves_dirs=get_fallback_saves_dirs(),
            get_events_db_path=get_events_db_path,
        )

    async def run_load_game(*, filename: str) -> dict:
        runtime = _runtime()
        from src.sim import get_save_info

        return await get_load_game_into_runtime()(
            runtime,
            filename=filename,
            saves_dir=get_config().paths.saves,
            fallback_saves_dirs=get_fallback_saves_dirs(),
            get_save_info=get_save_info,
            language_manager=language_manager,
            manager=manager,
            t=t,
            apply_runtime_content_locale=get_apply_runtime_content_locale(),
            scan_avatar_assets=lambda: avatar_assets.update(scan_avatar_assets(assets_path=assets_path)),
            load_game=get_load_game(),
            get_settings_service=get_settings_service,
            _model_to_dict=model_to_dict,
            room_registry=room_registry,
        )

    return SimpleNamespace(
        run_start_game=run_start_game,
        run_reinit_game=run_reinit_game,
        run_reset_game=run_reset_game,
        run_pause_game=run_pause_game,
        run_resume_game=run_resume_game,
        run_cleanup_events=run_cleanup_events,
        run_set_phenomenon=run_set_phenomenon,
        run_create_avatar=run_create_avatar,
        run_delete_avatar=run_delete_avatar,
        run_update_avatar_adjustment=run_update_avatar_adjustment,
        run_update_avatar_portrait=run_update_avatar_portrait,
        run_generate_custom_content=run_generate_custom_content,
        run_create_custom_content=run_create_custom_content,
        run_set_long_term_objective=run_set_long_term_objective,
        run_clear_long_term_objective=run_clear_long_term_objective,
        run_grant_avatar_support=run_grant_avatar_support,
        run_appoint_avatar_seed=run_appoint_avatar_seed,
        run_claim_sect=run_claim_sect,
        run_set_main_avatar=run_set_main_avatar,
        run_switch_control_seat=run_switch_control_seat,
        run_release_control_seat=run_release_control_seat,
        run_update_player_profile=run_update_player_profile,
        run_switch_world_room=run_switch_world_room,
        run_update_world_room_access=run_update_world_room_access,
        run_update_world_room_plan=run_update_world_room_plan,
        run_update_world_room_entitlement=run_update_world_room_entitlement,
        run_create_world_room_payment_order=run_create_world_room_payment_order,
        run_settle_world_room_payment=run_settle_world_room_payment,
        run_receive_sepay_world_room_payment_webhook=run_receive_sepay_world_room_payment_webhook,
        run_reconcile_world_room_payment=run_reconcile_world_room_payment,
        run_add_world_room_member=run_add_world_room_member,
        run_remove_world_room_member=run_remove_world_room_member,
        run_rotate_world_room_invite=run_rotate_world_room_invite,
        run_join_world_room_by_invite=run_join_world_room_by_invite,
        run_set_sect_directive=run_set_sect_directive,
        run_clear_sect_directive=run_clear_sect_directive,
        run_intervene_sect_relation=run_intervene_sect_relation,
        run_save_game=run_save_game,
        run_delete_save=run_delete_save,
        run_load_game=run_load_game,
    )
