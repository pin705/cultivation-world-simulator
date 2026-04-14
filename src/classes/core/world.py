from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any, Iterable
import uuid

from src.classes.environment.map import Map
from src.systems.time import Year, Month, MonthStamp
from src.sim.managers.avatar_manager import AvatarManager
from src.sim.managers.mortal_manager import MortalManager
from src.sim.managers.deceased_manager import DeceasedManager
from src.sim.managers.event_manager import EventManager
from src.classes.circulation import CirculationManager
from src.classes.gathering.gathering import GatheringManager
from src.classes.world_lore import WorldLore
from src.utils.df import game_configs
from src.classes.language import language_manager
from src.i18n import t
from src.classes.ranking import RankingManager
from src.classes.war import SectWar, STATUS_PEACE, STATUS_WAR
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.celestial_phenomenon import CelestialPhenomenon
    from src.classes.core.dynasty import Dynasty
    from src.classes.core.sect import Sect


@dataclass
class World():
    map: Map
    month_stamp: MonthStamp
    avatar_manager: AvatarManager = field(default_factory=AvatarManager)
    # 凡人管理器
    mortal_manager: MortalManager = field(default_factory=MortalManager)
    # 全局事件管理器
    event_manager: EventManager = field(default_factory=EventManager)
    # 已故角色档案管理器（独立于 AvatarManager，不受 cleanup 影响）
    deceased_manager: DeceasedManager = field(default_factory=DeceasedManager)
    # 当前天地灵机（世界级buff/debuff）
    current_phenomenon: Optional["CelestialPhenomenon"] = None
    # 当前王朝（凡人王朝）
    dynasty: Optional["Dynasty"] = None
    # 天地灵机开始年份（用于计算持续时间）
    phenomenon_start_year: int = 0
    # 出世物品流通管理器
    circulation: CirculationManager = field(default_factory=CirculationManager)
    # Gathering 管理器
    gathering_manager: GatheringManager = field(default_factory=GatheringManager)
    # 本局世界观与历史输入
    world_lore: "WorldLore" = field(default_factory=WorldLore)
    # 世界观塑形后的静态对象快照，用于存档/读档恢复
    world_lore_snapshot: dict[str, Any] = field(default_factory=dict)
    # 世界开始年份
    start_year: int = 0
    # 榜单管理器
    ranking_manager: RankingManager = field(default_factory=RankingManager)
    # 游玩单局 ID，用于区分存档
    playthrough_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # 玩家可用于异步干预世界的预算点数。
    player_intervention_points: int = field(
        default_factory=lambda: max(
            0,
            int(getattr(CONFIG.sect, "player_intervention_points_max", 3) or 0),
        )
    )
    active_controller_id: str = "local"
    player_control_seats: dict[str, dict[str, Any]] = field(default_factory=dict)
    player_profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    player_owned_sect_id: Optional[int] = None
    player_main_avatar_id: Optional[str] = None
    player_opening_choice_id: Optional[str] = None
    player_opening_choice_applied_month: int = -1
    player_relation_intervention_cooldowns: dict[str, int] = field(default_factory=dict)
    sect_relation_modifiers: list[dict[str, Any]] = field(default_factory=list)
    sect_wars: list[dict[str, Any]] = field(default_factory=list)
    # 宗门上下文（惰性初始化），用于统一本局启用宗门作用域
    _sect_context: Any = field(default=None, init=False, repr=False)

    def get_info(self, detailed: bool = False, avatar: Optional["Avatar"] = None) -> dict:
        """
        返回世界信息（dict），其中包含地图信息（dict）。
        如果指定了 avatar，将传给 map.get_info 用于过滤区域和计算距离。
        """
        static_info = self.static_info
        map_info = self.map.get_info(detailed=detailed, avatar=avatar)
        world_info = {**map_info, **static_info}

        if self.current_phenomenon:
            # 使用翻译 Key
            key = t("Current World Phenomenon")
            # 格式化内容，注意这里我们假设 name 和 desc 已经是当前语言的（它们是对象属性，加载时确定）
            # 但如果需要在 Prompt 中有特定的格式（如中文用【】，英文不用），也可以引入 key
            # 为了简单起见，我们把格式也放入翻译
            # "phenomenon_format": "【{name}】{desc}" (ZH) vs "{name}: {desc}" (EN)
            value = t("phenomenon_format", name=self.current_phenomenon.name, desc=self.current_phenomenon.desc)
            world_info[key] = value

        return world_info

    def get_avatars_in_same_region(self, avatar: "Avatar"):
        return self.avatar_manager.get_avatars_in_same_region(avatar)

    def get_observable_avatars(self, avatar: "Avatar"):
        return self.avatar_manager.get_observable_avatars(avatar)

    @property
    def sect_context(self) -> "SectContext":
        """
        提供统一的宗门作用域访问入口。
        - active_sects 默认来自 existed_sects；
        - 若不存在，则回退到全局 sects_by_id。
        """
        if self._sect_context is None:
            self._sect_context = SectContext(self)
            # 使用当前世界上的 existed_sects 初始化上下文（若存在）
            existed = getattr(self, "existed_sects", None)
            if existed:
                self._sect_context.from_existed_sects(existed)
        return self._sect_context

    @staticmethod
    def _normalize_sect_pair(sect_a_id: int, sect_b_id: int) -> tuple[int, int]:
        a = int(sect_a_id)
        b = int(sect_b_id)
        return (a, b) if a <= b else (b, a)

    def add_sect_relation_modifier(
        self,
        *,
        sect_a_id: int,
        sect_b_id: int,
        delta: int,
        duration: int,
        reason: str,
        meta: Optional[dict] = None,
    ) -> None:
        if int(duration) <= 0 or int(delta) == 0:
            return
        a, b = self._normalize_sect_pair(sect_a_id, sect_b_id)
        self.sect_relation_modifiers.append(
            {
                "sect_a_id": a,
                "sect_b_id": b,
                "delta": int(delta),
                "reason": str(reason),
                "meta": dict(meta or {}),
                "start_month": int(self.month_stamp),
                "duration": int(duration),
            }
        )

    def _iter_sect_wars(self) -> list[SectWar]:
        records: list[SectWar] = []
        for item in getattr(self, "sect_wars", []) or []:
            if isinstance(item, SectWar):
                records.append(item)
                continue
            if not isinstance(item, dict):
                continue
            try:
                records.append(SectWar.from_dict(item))
            except Exception:
                continue
        return records

    def _set_sect_wars(self, wars: Iterable[SectWar]) -> None:
        self.sect_wars = [war.to_dict() for war in wars]

    def get_sect_war(self, sect_a_id: int, sect_b_id: int) -> Optional[dict[str, Any]]:
        pair = SectWar.normalize_pair(sect_a_id, sect_b_id)
        for war in self._iter_sect_wars():
            if (int(war.sect_a_id), int(war.sect_b_id)) == pair:
                return war.to_dict()
        return None

    def are_sects_at_war(self, sect_a_id: int, sect_b_id: int) -> bool:
        war = self.get_sect_war(sect_a_id, sect_b_id)
        return bool(war and str(war.get("status", "")) == STATUS_WAR)

    def declare_sect_war(
        self,
        *,
        sect_a_id: int,
        sect_b_id: int,
        reason: str = "",
        start_month: Optional[int] = None,
    ) -> dict[str, Any]:
        pair = SectWar.normalize_pair(sect_a_id, sect_b_id)
        current_month = int(self.month_stamp if start_month is None else start_month)
        updated: list[SectWar] = []
        target: Optional[SectWar] = None
        for war in self._iter_sect_wars():
            if (int(war.sect_a_id), int(war.sect_b_id)) == pair:
                war.status = STATUS_WAR
                war.start_month = current_month
                war.reason = str(reason or war.reason or "")
                war.peace_start_month = None
                target = war
            updated.append(war)
        if target is None:
            target = SectWar.create(
                sect_a_id=pair[0],
                sect_b_id=pair[1],
                status=STATUS_WAR,
                current_month=current_month,
                reason=reason,
            )
            updated.append(target)
        self._set_sect_wars(updated)
        return target.to_dict()

    def make_sect_peace(
        self,
        *,
        sect_a_id: int,
        sect_b_id: int,
        reason: str = "",
        peace_start_month: Optional[int] = None,
    ) -> dict[str, Any]:
        pair = SectWar.normalize_pair(sect_a_id, sect_b_id)
        current_month = int(self.month_stamp if peace_start_month is None else peace_start_month)
        updated: list[SectWar] = []
        target: Optional[SectWar] = None
        for war in self._iter_sect_wars():
            if (int(war.sect_a_id), int(war.sect_b_id)) == pair:
                war.status = STATUS_PEACE
                war.peace_start_month = current_month
                war.reason = str(reason or war.reason or "")
                target = war
            updated.append(war)
        if target is None:
            target = SectWar.create(
                sect_a_id=pair[0],
                sect_b_id=pair[1],
                status=STATUS_PEACE,
                current_month=current_month,
                reason=reason,
                peace_start_month=current_month,
            )
            updated.append(target)
        self._set_sect_wars(updated)
        return target.to_dict()

    def record_sect_battle(self, sect_a_id: int, sect_b_id: int, *, battle_month: Optional[int] = None) -> None:
        pair = SectWar.normalize_pair(sect_a_id, sect_b_id)
        current_month = int(self.month_stamp if battle_month is None else battle_month)
        updated: list[SectWar] = []
        found = False
        for war in self._iter_sect_wars():
            if (int(war.sect_a_id), int(war.sect_b_id)) == pair:
                war.last_battle_month = current_month
                found = True
            updated.append(war)
        if not found:
            updated.append(
                SectWar.create(
                    sect_a_id=pair[0],
                    sect_b_id=pair[1],
                    status=STATUS_WAR,
                    current_month=current_month,
                    last_battle_month=current_month,
                )
            )
        self._set_sect_wars(updated)

    def get_sect_diplomacy_state(
        self,
        sect_a_id: int,
        sect_b_id: int,
        *,
        current_month: Optional[int] = None,
    ) -> dict[str, Any]:
        pair = SectWar.normalize_pair(sect_a_id, sect_b_id)
        war = self.get_sect_war(pair[0], pair[1])
        now = int(self.month_stamp if current_month is None else current_month)
        if war is None:
            peace_start = int(getattr(self, "start_year", 0)) * 12
            peace_months = max(0, now - peace_start)
            return {
                "status": STATUS_PEACE,
                "start_month": peace_start,
                "peace_start_month": peace_start,
                "peace_months": peace_months,
                "war_months": 0,
                "last_battle_month": None,
                "reason": "",
            }

        status = str(war.get("status", STATUS_PEACE) or STATUS_PEACE)
        war_start = int(war.get("start_month", now) or now)
        peace_start = war.get("peace_start_month")
        peace_start_int = int(peace_start) if peace_start is not None else None
        if status == STATUS_WAR:
            return {
                "status": STATUS_WAR,
                "start_month": war_start,
                "peace_start_month": None,
                "peace_months": 0,
                "war_months": max(0, now - war_start),
                "last_battle_month": war.get("last_battle_month"),
                "reason": str(war.get("reason", "") or ""),
            }

        effective_peace_start = peace_start_int if peace_start_int is not None else war_start
        return {
            "status": STATUS_PEACE,
            "start_month": war_start,
            "peace_start_month": effective_peace_start,
            "peace_months": max(0, now - effective_peace_start),
            "war_months": 0,
            "last_battle_month": war.get("last_battle_month"),
            "reason": str(war.get("reason", "") or ""),
        }

    def prune_expired_sect_relation_modifiers(self, current_month: Optional[int] = None) -> None:
        if not self.sect_relation_modifiers:
            return
        now = int(self.month_stamp if current_month is None else current_month)
        self.sect_relation_modifiers = [
            item
            for item in self.sect_relation_modifiers
            if now < int(item.get("start_month", 0)) + int(item.get("duration", 0))
        ]

    def get_active_sect_relation_breakdown(
        self, current_month: Optional[int] = None
    ) -> dict[tuple[int, int], list[dict[str, Any]]]:
        self.prune_expired_sect_relation_modifiers(current_month)
        result: dict[tuple[int, int], list[dict[str, Any]]] = {}
        for item in self.sect_relation_modifiers:
            pair = self._normalize_sect_pair(
                int(item.get("sect_a_id", 0)),
                int(item.get("sect_b_id", 0)),
            )
            if pair[0] <= 0 or pair[1] <= 0:
                continue
            result.setdefault(pair, []).append(
                {
                    "reason": str(item.get("reason", "")),
                    "delta": int(item.get("delta", 0)),
                    "meta": dict(item.get("meta", {}) or {}),
                }
            )
        return result

    def get_active_sect_diplomacy_breakdown(
        self,
        current_month: Optional[int] = None,
        sect_ids: Optional[Iterable[int]] = None,
    ) -> dict[tuple[int, int], list[dict[str, Any]]]:
        now = int(self.month_stamp if current_month is None else current_month)
        result: dict[tuple[int, int], list[dict[str, Any]]] = {}
        normalized_ids = sorted({int(sid) for sid in (sect_ids or []) if int(sid) > 0})
        for war in self._iter_sect_wars():
            pair = SectWar.normalize_pair(war.sect_a_id, war.sect_b_id)
            if pair[0] <= 0 or pair[1] <= 0:
                continue
            if war.status == STATUS_WAR:
                war_years = max(0, (now - int(war.start_month)) // 12)
                delta = -20 - min(20, war_years * 2)
                result.setdefault(pair, []).append(
                    {
                        "reason": "WAR_STATE",
                        "delta": delta,
                        "meta": {
                            "status": STATUS_WAR,
                            "war_months": max(0, now - int(war.start_month)),
                        },
                    }
                )
                continue

            peace_start = (
                int(war.peace_start_month)
                if war.peace_start_month is not None
                else int(war.start_month)
            )
            peace_months = max(0, now - peace_start)
            peace_bonus = min(20, peace_months // 12)
            result.setdefault(pair, []).append(
                {
                    "reason": "PEACE_STATE",
                    "delta": 0,
                    "meta": {
                        "status": STATUS_PEACE,
                        "peace_months": peace_months,
                    },
                }
            )
            if peace_bonus > 0:
                result[pair].append(
                    {
                        "reason": "LONG_PEACE",
                        "delta": peace_bonus,
                        "meta": {
                            "status": STATUS_PEACE,
                            "peace_months": peace_months,
                            "capped": peace_bonus >= 20,
                        },
                    }
                )
        if len(normalized_ids) >= 2:
            for idx in range(len(normalized_ids)):
                for jdx in range(idx + 1, len(normalized_ids)):
                    pair = (normalized_ids[idx], normalized_ids[jdx])
                    if pair in result:
                        continue
                    peace_start = int(getattr(self, "start_year", 0)) * 12
                    peace_months = max(0, now - peace_start)
                    peace_bonus = min(20, peace_months // 12)
                    result[pair] = [
                        {
                            "reason": "PEACE_STATE",
                            "delta": 0,
                            "meta": {
                                "status": STATUS_PEACE,
                                "peace_months": peace_months,
                            },
                        }
                    ]
                    if peace_bonus > 0:
                        result[pair].append(
                            {
                                "reason": "LONG_PEACE",
                                "delta": peace_bonus,
                                "meta": {
                                    "status": STATUS_PEACE,
                                    "peace_months": peace_months,
                                    "capped": peace_bonus >= 20,
                                },
                            }
                        )
        return result

    def set_world_lore(self, lore_text: str) -> None:
        """设置本局的世界观与历史输入文本。"""
        self.world_lore.text = lore_text

    @staticmethod
    def _get_player_intervention_points_max_from_config() -> int:
        sect_conf = getattr(CONFIG, "sect", None)
        return max(0, int(getattr(sect_conf, "player_intervention_points_max", 3) or 0))

    @staticmethod
    def _get_player_intervention_regen_from_config() -> int:
        sect_conf = getattr(CONFIG, "sect", None)
        return max(0, int(getattr(sect_conf, "player_intervention_points_regen_per_month", 1) or 0))

    @staticmethod
    def _get_player_directive_cost_from_config() -> int:
        sect_conf = getattr(CONFIG, "sect", None)
        return max(0, int(getattr(sect_conf, "player_directive_cost", 1) or 0))

    def get_player_intervention_points_max(self) -> int:
        return self._get_player_intervention_points_max_from_config()

    def get_player_intervention_regen_per_month(self) -> int:
        return self._get_player_intervention_regen_from_config()

    def get_player_directive_cost(self) -> int:
        return self._get_player_directive_cost_from_config()

    def _normalize_controller_id(self, controller_id: str | None = None) -> str:
        normalized = str(controller_id or getattr(self, "active_controller_id", "local") or "local").strip()
        return normalized or "local"

    @staticmethod
    def _normalize_viewer_id(viewer_id: str | None) -> str:
        normalized = str(viewer_id or "").strip()
        return normalized

    @staticmethod
    def _normalize_player_display_name(display_name: str | None) -> str:
        normalized = " ".join(str(display_name or "").split())
        return normalized[:24]

    def _build_default_player_control_state(self) -> dict[str, Any]:
        return {
            "intervention_points": self.get_player_intervention_points_max(),
            "holder_id": None,
            "owned_sect_id": None,
            "main_avatar_id": None,
            "opening_choice_id": None,
            "opening_choice_applied_month": -1,
            "relation_intervention_cooldowns": {},
        }

    def _build_default_player_profile_state(self) -> dict[str, Any]:
        current_month = int(self.month_stamp)
        return {
            "display_name": "",
            "joined_month": current_month,
            "last_seen_month": current_month,
        }

    def _normalize_player_control_state(self, state: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        normalized = dict(self._build_default_player_control_state())
        normalized.update(dict(state or {}))

        try:
            normalized["intervention_points"] = max(
                0,
                min(
                    self.get_player_intervention_points_max(),
                    int(normalized.get("intervention_points", 0) or 0),
                ),
            )
        except (TypeError, ValueError):
            normalized["intervention_points"] = self.get_player_intervention_points_max()

        holder_id = str(normalized.get("holder_id", "") or "").strip() or None
        normalized["holder_id"] = holder_id

        owned_sect_id = normalized.get("owned_sect_id")
        try:
            owned_sect_id = int(owned_sect_id) if owned_sect_id is not None else None
        except (TypeError, ValueError):
            owned_sect_id = None

        active_sects = getattr(self, "existed_sects", []) or []
        if owned_sect_id is not None and not any(
            int(getattr(sect, "id", -1)) == owned_sect_id for sect in active_sects
        ):
            owned_sect_id = None
        normalized["owned_sect_id"] = owned_sect_id

        main_avatar_id = str(normalized.get("main_avatar_id", "") or "").strip() or None
        if main_avatar_id:
            avatar = getattr(self.avatar_manager, "avatars", {}).get(main_avatar_id)
            avatar_sect_id = getattr(getattr(avatar, "sect", None), "id", None) if avatar is not None else None
            if (
                avatar is None
                or bool(getattr(avatar, "is_dead", False))
                or owned_sect_id is None
                or avatar_sect_id is None
                or int(avatar_sect_id) != int(owned_sect_id)
            ):
                main_avatar_id = None
        normalized["main_avatar_id"] = main_avatar_id
        opening_choice_id = str(normalized.get("opening_choice_id", "") or "").strip() or None
        try:
            opening_choice_applied_month = int(
                normalized.get("opening_choice_applied_month", -1)
            )
        except (TypeError, ValueError):
            opening_choice_applied_month = -1
        if owned_sect_id is None:
            opening_choice_id = None
            opening_choice_applied_month = -1
        normalized["opening_choice_id"] = opening_choice_id
        normalized["opening_choice_applied_month"] = (
            opening_choice_applied_month if opening_choice_id else -1
        )
        normalized["relation_intervention_cooldowns"] = dict(
            normalized.get("relation_intervention_cooldowns", {}) or {}
        )
        return normalized

    def _normalize_player_profile_state(
        self,
        viewer_id: str,
        state: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            raise ValueError("viewer_id is required")

        normalized = dict(self._build_default_player_profile_state())
        normalized.update(dict(state or {}))
        normalized["display_name"] = self._normalize_player_display_name(normalized.get("display_name"))

        default_month = int(self.month_stamp)
        try:
            joined_month = int(normalized.get("joined_month", default_month) or default_month)
        except (TypeError, ValueError):
            joined_month = default_month
        try:
            last_seen_month = int(normalized.get("last_seen_month", joined_month) or joined_month)
        except (TypeError, ValueError):
            last_seen_month = joined_month
        normalized["joined_month"] = joined_month
        normalized["last_seen_month"] = max(joined_month, last_seen_month)
        return normalized

    def ensure_player_profile(
        self,
        viewer_id: str | None,
        *,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            raise ValueError("viewer_id is required")
        if not isinstance(getattr(self, "player_profiles", None), dict):
            self.player_profiles = {}

        state = self.player_profiles.get(normalized_viewer_id)
        normalized = self._normalize_player_profile_state(normalized_viewer_id, state)
        if display_name is not None:
            normalized["display_name"] = self._normalize_player_display_name(display_name)
        self.player_profiles[normalized_viewer_id] = normalized
        return dict(normalized)

    def touch_player_profile(self, viewer_id: str | None) -> dict[str, Any] | None:
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            return None
        state = self.ensure_player_profile(normalized_viewer_id)
        state["last_seen_month"] = int(self.month_stamp)
        self.player_profiles[normalized_viewer_id] = self._normalize_player_profile_state(
            normalized_viewer_id,
            state,
        )
        return dict(self.player_profiles[normalized_viewer_id])

    def set_player_profile_display_name(self, viewer_id: str | None, display_name: str | None) -> dict[str, Any]:
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            raise ValueError("viewer_id is required")
        state = self.ensure_player_profile(normalized_viewer_id, display_name=display_name)
        state["last_seen_month"] = int(self.month_stamp)
        self.player_profiles[normalized_viewer_id] = self._normalize_player_profile_state(
            normalized_viewer_id,
            state,
        )
        return dict(self.player_profiles[normalized_viewer_id])

    def get_player_profile(self, viewer_id: str | None) -> Optional[dict[str, Any]]:
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            return None
        state = dict(getattr(self, "player_profiles", {}) or {}).get(normalized_viewer_id)
        if state is None:
            return None
        return dict(self._normalize_player_profile_state(normalized_viewer_id, state))

    def export_player_profiles(self) -> dict[str, dict[str, Any]]:
        if not isinstance(getattr(self, "player_profiles", None), dict):
            self.player_profiles = {}
        viewer_ids = {
            viewer_id
            for viewer_id in self.player_profiles.keys()
            if self._normalize_viewer_id(viewer_id)
        }
        viewer_ids.update(
            {
                holder_id
                for holder_id in (
                    self.get_player_control_seat_holder(controller_id)
                    for controller_id in self.list_player_control_seat_ids()
                )
                if holder_id
            }
        )
        result: dict[str, dict[str, Any]] = {}
        for viewer_id in sorted(viewer_ids):
            result[viewer_id] = self._normalize_player_profile_state(
                viewer_id,
                self.player_profiles.get(viewer_id),
            )
        return result

    def load_player_profiles(self, profiles: Optional[dict[str, Any]]) -> None:
        normalized: dict[str, dict[str, Any]] = {}
        for viewer_id, state in dict(profiles or {}).items():
            normalized_viewer_id = self._normalize_viewer_id(viewer_id)
            if not normalized_viewer_id:
                continue
            normalized[normalized_viewer_id] = self._normalize_player_profile_state(
                normalized_viewer_id,
                state if isinstance(state, dict) else {},
            )
        self.player_profiles = normalized

    def get_player_profile_summary(self, viewer_id: str | None) -> Optional[dict[str, Any]]:
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            return None
        profile = self.get_player_profile(normalized_viewer_id)
        controller_id = self.find_player_control_seat_by_holder(normalized_viewer_id)
        if profile is None and controller_id is None:
            return None
        profile_state = profile or self._normalize_player_profile_state(normalized_viewer_id)
        seat = self.ensure_player_control_seat(controller_id) if controller_id else {}
        return {
            "viewer_id": normalized_viewer_id,
            "display_name": str(profile_state.get("display_name", "") or ""),
            "joined_month": int(profile_state.get("joined_month", int(self.month_stamp)) or int(self.month_stamp)),
            "last_seen_month": int(profile_state.get("last_seen_month", int(self.month_stamp)) or int(self.month_stamp)),
            "controller_id": controller_id,
            "owned_sect_id": seat.get("owned_sect_id"),
            "main_avatar_id": seat.get("main_avatar_id"),
            "is_active_controller": bool(controller_id and controller_id == self.get_active_controller_id()),
        }

    def list_player_profiles(self) -> list[dict[str, Any]]:
        viewer_ids = {
            viewer_id
            for viewer_id in (getattr(self, "player_profiles", {}) or {}).keys()
            if self._normalize_viewer_id(viewer_id)
        }
        viewer_ids.update(
            {
                holder_id
                for holder_id in (
                    self.get_player_control_seat_holder(controller_id)
                    for controller_id in self.list_player_control_seat_ids()
                )
                if holder_id
            }
        )
        summaries = [
            summary
            for summary in (self.get_player_profile_summary(viewer_id) for viewer_id in sorted(viewer_ids))
            if summary is not None
        ]
        summaries.sort(
            key=lambda item: (
                0 if item.get("is_active_controller") else 1,
                str(item.get("display_name", "") or "").lower(),
                str(item.get("viewer_id", "")),
            )
        )
        return summaries

    def ensure_player_control_seat(self, controller_id: str | None = None) -> dict[str, Any]:
        cid = self._normalize_controller_id(controller_id)
        if not isinstance(getattr(self, "player_control_seats", None), dict):
            self.player_control_seats = {}

        state = self.player_control_seats.get(cid)
        if state is None and cid == self._normalize_controller_id():
            state = {
                "intervention_points": int(getattr(self, "player_intervention_points", 0) or 0),
                "holder_id": None,
                "owned_sect_id": self.get_player_owned_sect_id(),
                "main_avatar_id": self.get_player_main_avatar_id(),
                "opening_choice_id": self.get_player_opening_choice_id(),
                "opening_choice_applied_month": self.get_player_opening_choice_applied_month(),
                "relation_intervention_cooldowns": dict(
                    getattr(self, "player_relation_intervention_cooldowns", {}) or {}
                ),
            }
        normalized = self._normalize_player_control_state(state)
        self.player_control_seats[cid] = normalized
        return normalized

    def export_player_control_seats(self) -> dict[str, dict[str, Any]]:
        self.sync_active_player_control_seat()
        result: dict[str, dict[str, Any]] = {}
        for controller_id in sorted(self.player_control_seats.keys()):
            result[controller_id] = self._normalize_player_control_state(
                self.player_control_seats.get(controller_id)
            )
        if not result:
            cid = self._normalize_controller_id()
            result[cid] = self.ensure_player_control_seat(cid)
        return result

    def sync_active_player_control_seat(self) -> None:
        cid = self._normalize_controller_id()
        self.player_control_seats[cid] = self._normalize_player_control_state(
            {
                "intervention_points": int(getattr(self, "player_intervention_points", 0) or 0),
                "holder_id": self.get_player_control_seat_holder(cid),
                "owned_sect_id": self.get_player_owned_sect_id(),
                "main_avatar_id": self.get_player_main_avatar_id(),
                "opening_choice_id": self.get_player_opening_choice_id(),
                "opening_choice_applied_month": self.get_player_opening_choice_applied_month(),
                "relation_intervention_cooldowns": dict(
                    getattr(self, "player_relation_intervention_cooldowns", {}) or {}
                ),
            }
        )

    def get_active_controller_id(self) -> str:
        return self._normalize_controller_id()

    def get_player_control_seat_holder(self, controller_id: str | None = None) -> Optional[str]:
        seat = self.ensure_player_control_seat(controller_id)
        holder_id = str(seat.get("holder_id", "") or "").strip()
        return holder_id or None

    def is_player_control_seat_claimed(self, controller_id: str | None = None) -> bool:
        return self.get_player_control_seat_holder(controller_id) is not None

    def is_player_control_seat_owned_by(self, controller_id: str | None, viewer_id: str | None) -> bool:
        normalized_viewer_id = str(viewer_id or "").strip()
        if not normalized_viewer_id:
            return False
        return self.get_player_control_seat_holder(controller_id) == normalized_viewer_id

    def find_player_control_seat_by_holder(self, viewer_id: str | None) -> Optional[str]:
        normalized_viewer_id = str(viewer_id or "").strip()
        if not normalized_viewer_id:
            return None
        for controller_id in self.list_player_control_seat_ids():
            if self.get_player_control_seat_holder(controller_id) == normalized_viewer_id:
                return controller_id
        return None

    def claim_player_control_seat(self, controller_id: str | None, viewer_id: str) -> dict[str, Any]:
        cid = self._normalize_controller_id(controller_id)
        normalized_viewer_id = self._normalize_viewer_id(viewer_id)
        if not normalized_viewer_id:
            raise ValueError("viewer_id is required")
        self.touch_player_profile(normalized_viewer_id)
        current_controller_id = self.find_player_control_seat_by_holder(normalized_viewer_id)
        if current_controller_id is not None and current_controller_id != cid:
            previous_seat = self.ensure_player_control_seat(current_controller_id)
            previous_seat["holder_id"] = None
            self.player_control_seats[current_controller_id] = self._normalize_player_control_state(previous_seat)
        seat = self.ensure_player_control_seat(cid)
        seat["holder_id"] = normalized_viewer_id
        self.player_control_seats[cid] = self._normalize_player_control_state(seat)
        return self.ensure_player_control_seat(cid)

    def release_player_control_seat(self, controller_id: str | None) -> dict[str, Any]:
        cid = self._normalize_controller_id(controller_id)
        seat = self.ensure_player_control_seat(cid)
        seat["holder_id"] = None
        self.player_control_seats[cid] = self._normalize_player_control_state(seat)
        return self.ensure_player_control_seat(cid)

    def list_player_control_seat_summaries(self) -> list[dict[str, Any]]:
        self.sync_active_player_control_seat()
        return [
            {
                "id": controller_id,
                "holder_id": self.get_player_control_seat_holder(controller_id),
                "holder_display_name": (
                    self.get_player_profile_summary(self.get_player_control_seat_holder(controller_id)) or {}
                ).get("display_name", ""),
                "owned_sect_id": self.ensure_player_control_seat(controller_id).get("owned_sect_id"),
                "main_avatar_id": self.ensure_player_control_seat(controller_id).get("main_avatar_id"),
                "opening_choice_id": self.ensure_player_control_seat(controller_id).get("opening_choice_id"),
                "is_active": controller_id == self.get_active_controller_id(),
            }
            for controller_id in self.list_player_control_seat_ids()
        ]

    def list_player_control_seat_ids(self) -> list[str]:
        self.sync_active_player_control_seat()
        return sorted(set((self.player_control_seats or {}).keys()) | {self.get_active_controller_id()})

    def switch_active_controller(self, controller_id: str | None) -> dict[str, Any]:
        self.sync_active_player_control_seat()
        cid = self._normalize_controller_id(controller_id)
        state = self.ensure_player_control_seat(cid)
        self.active_controller_id = cid
        self.player_intervention_points = int(state.get("intervention_points", 0) or 0)
        self.player_owned_sect_id = state.get("owned_sect_id")
        self.player_main_avatar_id = state.get("main_avatar_id")
        self.player_opening_choice_id = state.get("opening_choice_id")
        self.player_opening_choice_applied_month = int(
            state.get("opening_choice_applied_month", -1)
        )
        self.player_relation_intervention_cooldowns = dict(
            state.get("relation_intervention_cooldowns", {}) or {}
        )
        self.refresh_player_control_bindings()
        return self.ensure_player_control_seat(cid)

    def load_player_control_seats(
        self,
        seats: Optional[dict[str, Any]],
        *,
        active_controller_id: str | None = None,
    ) -> None:
        normalized: dict[str, dict[str, Any]] = {}
        for controller_id, state in dict(seats or {}).items():
            cid = self._normalize_controller_id(str(controller_id))
            normalized[cid] = self._normalize_player_control_state(state if isinstance(state, dict) else {})
        self.player_control_seats = normalized
        self.switch_active_controller(active_controller_id or self.active_controller_id or "local")

    def get_player_owned_sect_id(self) -> Optional[int]:
        try:
            if self.player_owned_sect_id is None:
                return None
            return int(self.player_owned_sect_id)
        except (TypeError, ValueError):
            return None

    def get_player_main_avatar_id(self) -> Optional[str]:
        value = str(getattr(self, "player_main_avatar_id", "") or "").strip()
        return value or None

    def get_player_opening_choice_id(self) -> Optional[str]:
        value = str(getattr(self, "player_opening_choice_id", "") or "").strip()
        return value or None

    def get_player_opening_choice_applied_month(self) -> int:
        try:
            return int(getattr(self, "player_opening_choice_applied_month", -1))
        except (TypeError, ValueError):
            return -1

    def has_player_opening_choice(self) -> bool:
        return self.get_player_opening_choice_id() is not None

    def has_player_owned_sect(self) -> bool:
        return self.get_player_owned_sect_id() is not None

    def is_player_owned_sect(self, sect_id: int | str | None) -> bool:
        owned = self.get_player_owned_sect_id()
        if owned is None or sect_id is None:
            return False
        try:
            return owned == int(sect_id)
        except (TypeError, ValueError):
            return False

    def is_player_main_avatar(self, avatar_id: str | None) -> bool:
        current_main = self.get_player_main_avatar_id()
        return bool(current_main and avatar_id and current_main == str(avatar_id))

    def set_player_owned_sect(self, sect_id: int | None) -> None:
        if sect_id is None:
            self.player_owned_sect_id = None
            self.player_main_avatar_id = None
            self.player_opening_choice_id = None
            self.player_opening_choice_applied_month = -1
            self.sync_active_player_control_seat()
            return
        new_sect_id = int(sect_id)
        if self.get_player_owned_sect_id() != new_sect_id:
            self.player_opening_choice_id = None
            self.player_opening_choice_applied_month = -1
        self.player_owned_sect_id = new_sect_id
        self.sync_active_player_control_seat()

    def set_player_main_avatar(self, avatar_id: str | None) -> None:
        normalized = str(avatar_id or "").strip()
        self.player_main_avatar_id = normalized or None
        self.sync_active_player_control_seat()

    def set_player_opening_choice(
        self,
        choice_id: str | None,
        *,
        applied_month: int | None = None,
    ) -> None:
        normalized_choice_id = str(choice_id or "").strip() or None
        self.player_opening_choice_id = normalized_choice_id
        if normalized_choice_id is None:
            self.player_opening_choice_applied_month = -1
        else:
            try:
                self.player_opening_choice_applied_month = int(
                    self.month_stamp if applied_month is None else applied_month
                )
            except (TypeError, ValueError):
                self.player_opening_choice_applied_month = int(self.month_stamp)
        self.sync_active_player_control_seat()

    def is_avatar_in_player_owned_sect(self, avatar: Optional["Avatar"]) -> bool:
        if avatar is None:
            return False
        sect = getattr(avatar, "sect", None)
        if sect is None:
            return False
        return self.is_player_owned_sect(getattr(sect, "id", None))

    def refresh_player_control_bindings(self) -> None:
        self.sync_active_player_control_seat()
        normalized_seats = {
            controller_id: self._normalize_player_control_state(state)
            for controller_id, state in dict(getattr(self, "player_control_seats", {}) or {}).items()
        }
        self.player_control_seats = normalized_seats
        active_state = self.ensure_player_control_seat(self.get_active_controller_id())
        self.player_intervention_points = int(active_state.get("intervention_points", 0) or 0)
        self.player_owned_sect_id = active_state.get("owned_sect_id")
        self.player_main_avatar_id = active_state.get("main_avatar_id")
        self.player_opening_choice_id = active_state.get("opening_choice_id")
        self.player_opening_choice_applied_month = int(
            active_state.get("opening_choice_applied_month", -1)
        )
        self.player_relation_intervention_cooldowns = dict(
            active_state.get("relation_intervention_cooldowns", {}) or {}
        )

    def set_player_intervention_points(self, value: int | float) -> None:
        cap = self.get_player_intervention_points_max()
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            normalized = 0
        self.player_intervention_points = max(0, min(cap, normalized))
        self.sync_active_player_control_seat()

    def change_player_intervention_points(self, delta: int | float) -> None:
        self.set_player_intervention_points(int(self.player_intervention_points) + int(delta))

    def refill_player_intervention_points(self) -> None:
        self.set_player_intervention_points(self.get_player_intervention_points_max())

    def regenerate_player_intervention_points(self) -> None:
        regen = self.get_player_intervention_regen_per_month()
        if regen <= 0:
            return
        self.sync_active_player_control_seat()
        for controller_id in self.list_player_control_seat_ids():
            seat = self.ensure_player_control_seat(controller_id)
            seat["intervention_points"] = max(
                0,
                min(
                    self.get_player_intervention_points_max(),
                    int(seat.get("intervention_points", 0) or 0) + regen,
                ),
            )
            self.player_control_seats[controller_id] = seat
        active_state = self.ensure_player_control_seat(self.get_active_controller_id())
        self.player_intervention_points = int(active_state.get("intervention_points", 0) or 0)

    @property
    def static_info(self) -> dict:
        info_list = game_configs.get("world_info", [])
        desc = {}
        for row in info_list:
            t_val = row.get("title")
            d_val = row.get("desc")
            if t_val and d_val:
                desc[t_val] = d_val
        return desc

    @classmethod
    def create_with_db(
        cls,
        map: "Map",
        month_stamp: MonthStamp,
        events_db_path: Path,
        start_year: int = 0,
    ) -> "World":
        """
        工厂方法：创建使用 SQLite 持久化事件的 World 实例。

        Args:
            map: 地图对象。
            month_stamp: 时间戳。
            events_db_path: 事件数据库文件路径。
            start_year: 世界开始年份。

        Returns:
            配置好的 World 实例。
        """
        event_manager = EventManager.create_with_db(events_db_path)
        world = cls(
            map=map,
            month_stamp=month_stamp,
            event_manager=event_manager,
            start_year=start_year,
        )
        
        # 初始化天下武道会的时间
        world.ranking_manager.init_tournament_info(
            start_year,
            month_stamp.get_year(),
            month_stamp.get_month().value
        )
        world.refill_player_intervention_points()
        
        return world


class SectContext:
    """
    本局宗门上下文。
    负责维护“本局启用且仍存续的宗门 ID 集合”，并提供统一的 active 宗门读取入口。
    """

    def __init__(self, world: World):
        self._world = world
        self.active_sect_ids: set[int] = set()

    def from_existed_sects(self, existed_sects: Iterable["Sect"]) -> None:
        """根据本局启用宗门列表初始化 active_sect_ids。"""
        self.active_sect_ids = {
            int(getattr(sect, "id", 0))
            for sect in existed_sects
            if getattr(sect, "is_active", True)
        }

    def mark_sect_inactive(self, sect_id: int) -> None:
        """在上下文中标记某宗门为失效。"""
        try:
            sid = int(sect_id)
        except (TypeError, ValueError):
            return
        self.active_sect_ids.discard(sid)

    def get_active_sects(self) -> list["Sect"]:
        """
        返回当前本局仍然激活的宗门列表。
        优先使用 world.existed_sects（保持与当前局实际挂载的 Sect 实例一致），
        再结合 active_sect_ids 做过滤；若不存在，则回退到全局 sects_by_id。
        """
        from src.classes.core.sect import sects_by_id
        existed = getattr(self._world, "existed_sects", None) or []

        # 1. 若世界上存在显式的 existed_sects，则以其为主（保持与当前局实例一致）
        if existed:
            if self.active_sect_ids:
                return [
                    sect
                    for sect in existed
                    if int(getattr(sect, "id", 0)) in self.active_sect_ids
                    and getattr(sect, "is_active", True)
                ]
            return [sect for sect in existed if getattr(sect, "is_active", True)]

        # 2. 不存在 existed_sects 时，再根据 active_sect_ids 过滤全局 sects_by_id
        if self.active_sect_ids:
            return [
                sect
                for sid, sect in sects_by_id.items()
                if sid in self.active_sect_ids and getattr(sect, "is_active", True)
            ]

        # 3. 最后回退到全局 sects_by_id 的激活宗门
        return [sect for sect in sects_by_id.values() if getattr(sect, "is_active", True)]
