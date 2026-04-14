/**
 * API 数据传输对象 (Data Transfer Objects)
 * 这些类型严格对应后端接口返回的 JSON 结构。
 */

import type { AppLocale } from '../locales/registry';
import type {
  MapMatrix,
  CelestialPhenomenon,
  HiddenDomainInfo,
  AvatarDetail,
  RegionDetail,
  SectDetail,
  EffectEntity,
} from './core';

// --- 通用响应 ---

export interface ApiResponse<T> {
  status: 'ok' | 'error';
  message?: string;
  data?: T; // 有些接口直接把数据铺平在顶层，需根据实际情况调整
}

export interface AuthSessionDTO {
  session_id: string;
  viewer_id: string;
  previous_viewer_id?: string | null;
  auth_type: string;
  display_name: string;
  email?: string | null;
  has_password_account?: boolean;
  created_at: string;
  updated_at: string;
  last_seen_at: string;
  session_created_at: string;
  session_updated_at: string;
  session_last_seen_at: string;
  user_agent: string;
  is_new_session?: boolean;
  is_new_player?: boolean;
}

export interface AuthSessionStateDTO {
  authenticated: boolean;
  session: AuthSessionDTO | null;
  status?: string;
  message?: string;
}

export interface AuthSessionBootstrapDTO extends AuthSessionStateDTO {}

// --- 具体接口响应 ---

export interface InitialStateDTO {
  status: 'ok' | 'error';
  year: number;
  month: number;
  avatars?: Array<{
    id: string;
    name?: string;
    x: number;
    y: number;
    action?: string;
    gender?: string;
    pic_id?: number;
  }>;
  events?: EventDTO[];
  phenomenon?: CelestialPhenomenon | null;
  active_domains?: HiddenDomainInfo[];
}

export interface TickPayloadDTO {
  type: 'tick';
  room_id?: string;
  year: number;
  month: number;
  avatars?: Array<Partial<InitialStateDTO['avatars'] extends (infer U)[] ? U : never>>;
  events?: EventDTO[];
  phenomenon?: CelestialPhenomenon | null;
  active_domains?: HiddenDomainInfo[];
}

export interface MapResponseDTO {
  data: MapMatrix;
  regions: Array<{
    id: string | number;
    name: string;
    x: number;
    y: number;
    type: string;
    sect_id?: number;
    sect_name?: string;
    sect_is_active?: boolean;
    sect_color?: string;
    sub_type?: string;
  }>;
  render_config?: MapRenderConfigDTO;
}

// --- Detail 接口 ---

// 目前后端 /api/v1/query/detail 直接返回 Avatar/Region/Sect 的结构化信息，
// 在 P0 阶段我们先复用前端领域模型作为 DTO 类型，后续若后端结构调整再拆分。
export type AvatarDetailDTO = AvatarDetail;
export type RegionDetailDTO = RegionDetail;
export type SectDetailDTO = SectDetail;

export type DetailResponseDTO =
  | AvatarDetailDTO
  | RegionDetailDTO
  | SectDetailDTO;

export interface MapRenderConfigDTO {
  water_speed?: 'none' | 'low' | 'medium' | 'high';
  cloud_frequency?: 'none' | 'low' | 'high';
}

export interface SaveFileDTO {
  filename: string;
  save_time: string;
  game_time: string;
  version: string;
  // 新增字段。
  language: string;
  avatar_count: number;
  alive_count: number;
  dead_count: number;
  custom_name: string | null;
  event_count: number;
  is_auto_save: boolean;
  playthrough_id?: string;
}

// --- Game Data Metadata ---

export interface GameDataDTO {
  sects: Array<{ id: number; name: string; alignment: string }>;
  personas: Array<{ id: number; name: string; desc: string; rarity: string }>;
  realms: string[];
  techniques: Array<{ id: number; name: string; grade: string; attribute: string; sect: string | null }>;
  weapons: Array<{ id: number; name: string; grade: string; type: string }>;
  auxiliaries: Array<{ id: number; name: string; grade: string }>;
  alignments: Array<{ value: string; label: string }>;
}

export interface SimpleAvatarDTO {
  id: string;
  name: string;
  sect_name: string;
  realm: string;
  gender: string;
  age: number;
}

export interface CreateAvatarParams {
  surname?: string;
  given_name?: string;
  gender?: string;
  age?: number;
  level?: number;
  sect_id?: number;
  persona_ids?: number[];
  pic_id?: number;
  technique_id?: number;
  weapon_id?: number;
  auxiliary_id?: number;
  alignment?: string;
  appearance?: number;
  relations?: Array<{ target_id: string; relation: string }>;
}

export interface AvatarAdjustOptionDTO extends EffectEntity {
  id: string;
}

export interface AvatarAdjustCatalogDTO {
  techniques: AvatarAdjustOptionDTO[];
  weapons: AvatarAdjustOptionDTO[];
  auxiliaries: AvatarAdjustOptionDTO[];
  personas: AvatarAdjustOptionDTO[];
  goldfingers: AvatarAdjustOptionDTO[];
}

export interface UpdateAvatarAdjustmentParams {
  avatar_id: string;
  category: 'technique' | 'weapon' | 'auxiliary' | 'personas' | 'goldfinger';
  target_id?: number | null;
  persona_ids?: number[];
}

export interface UpdateAvatarPortraitParams {
  avatar_id: string;
  pic_id: number;
}

export interface AppointAvatarSeedParams {
  avatar_id: string;
}

export interface SetMainAvatarParams {
  avatar_id: string;
}

export interface ClaimSectParams {
  sect_id: number;
}

export interface ChoosePlayerOpeningParams {
  choice_id: string;
  viewer_id?: string;
}

export interface SwitchControlSeatParams {
  controller_id: string;
  viewer_id: string;
}

export interface ReleaseControlSeatParams {
  controller_id: string;
  viewer_id: string;
}

export interface UpdatePlayerProfileParams {
  display_name: string;
  viewer_id?: string;
}

export interface TransferPlayerIdentityParams {
  source_viewer_id: string;
  preferred_display_name?: string;
  viewer_id?: string;
}

export interface SwitchWorldRoomParams {
  room_id: string;
  viewer_id?: string;
}

export interface UpdateWorldRoomAccessParams {
  room_id: string;
  access_mode: 'open' | 'private';
  viewer_id?: string;
}

export interface UpdateWorldRoomPlanParams {
  room_id: string;
  plan_id: string;
  viewer_id?: string;
}

export interface UpdateWorldRoomEntitlementParams {
  room_id: string;
  billing_status: 'trial' | 'active' | 'grace' | 'expired';
  entitled_plan_id: string;
  viewer_id?: string;
}

export interface CreateWorldRoomPaymentOrderParams {
  room_id: string;
  target_plan_id: string;
  viewer_id?: string;
}

export interface SettleWorldRoomPaymentParams {
  room_id: string;
  order_id: string;
  payment_ref?: string;
  amount_vnd?: number;
  viewer_id?: string;
}

export interface ReconcileWorldRoomPaymentParams {
  transfer_note: string;
  amount_vnd?: number;
  payment_ref?: string;
  viewer_id?: string;
}

export interface UpdateWorldRoomMemberParams {
  room_id: string;
  member_viewer_id: string;
  viewer_id?: string;
}

export interface RotateWorldRoomInviteParams {
  room_id: string;
  viewer_id?: string;
}

export interface JoinWorldRoomByInviteParams {
  room_id: string;
  invite_code: string;
  viewer_id?: string;
}

export interface GenerateCustomContentParams {
  category: 'technique' | 'weapon' | 'auxiliary' | 'goldfinger';
  realm?: string;
  user_prompt: string;
}

export interface CustomContentDraftDTO extends AvatarAdjustOptionDTO {
  category: 'technique' | 'weapon' | 'auxiliary' | 'goldfinger';
  realm?: string;
  effects: Record<string, number | boolean>;
  weapon_type?: string;
  story_prompt?: string;
  mechanism_type?: string;
  is_custom?: boolean;
}

export interface CreateCustomContentParams {
  category: 'technique' | 'weapon' | 'auxiliary' | 'goldfinger';
  draft: CustomContentDraftDTO;
}

export interface GrantAvatarSupportParams {
  avatar_id: string;
}

export interface SetSectDirectiveParams {
  sect_id: number;
  content: string;
}

export interface ClearSectDirectiveParams {
  sect_id: number;
}

export interface InterveneSectRelationParams {
  sect_id: number;
  other_sect_id: number;
  mode: 'ease' | 'escalate';
}

export interface PhenomenonDTO {
  id: number;
  name: string;
  desc: string;
  rarity: string;
  duration_years: number;
  effect_desc: string;
}

// --- Config ---

export interface AudioSettingsDTO {
  bgm_volume: number;
  sfx_volume: number;
}

export interface UISettingsDTO {
  locale: AppLocale | string;
  audio: AudioSettingsDTO;
}

export interface SimulationSettingsDTO {
  auto_save_enabled: boolean;
  max_auto_saves: number;
}

export interface LLMConfigViewDTO {
  base_url: string;
  model_name: string;
  fast_model_name: string;
  mode: string;
  commercial_profile: string;
  max_concurrent_requests: number;
  has_api_key: boolean;
  api_format: string;
}

export interface LLMConfigDTO {
  base_url: string;
  api_key?: string;
  model_name: string;
  fast_model_name: string;
  mode: string;
  commercial_profile: string;
  max_concurrent_requests: number;
  clear_api_key?: boolean;
  api_format: string;
}

export interface RunConfigDTO {
  content_locale: AppLocale | string;
  init_npc_num: number;
  sect_num: number;
  npc_awakening_rate_per_month: number;
  world_lore?: string;
}

export interface AppSettingsDTO {
  schema_version: number;
  ui: UISettingsDTO;
  simulation: SimulationSettingsDTO;
  llm: {
    profile: LLMConfigViewDTO;
  };
  new_game_defaults: RunConfigDTO;
}

export interface AppSettingsPatchDTO {
  ui?: {
    locale?: UISettingsDTO['locale'];
    audio?: Partial<AudioSettingsDTO>;
  };
  simulation?: Partial<SimulationSettingsDTO>;
  new_game_defaults?: Partial<RunConfigDTO>;
}

// --- Events ---

export interface EventDTO {
  id: string;
  text: string;
  content: string;
  year: number;
  month: number;
  month_stamp: number;
  related_avatar_ids: string[];
  related_sects?: number[];
  is_major: boolean;
  is_story: boolean;
  render_key?: string;
  render_params?: Record<string, string | number | boolean | null>;
  created_at: number;
}

export interface EventsResponseDTO {
  events: EventDTO[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface FetchEventsParams {
  avatar_id?: string;
  avatar_id_1?: string;
  avatar_id_2?: string;
  sect_id?: number;
  major_scope?: 'all' | 'major' | 'minor';
  cursor?: string;
  limit?: number;
}

// --- Status ---

export interface PlayerOnboardingSectDTO {
  id: number;
  name: string;
  member_count: number;
  is_owned: boolean;
  can_claim: boolean;
}

export interface PlayerOnboardingAvatarDTO {
  id: string;
  name: string;
  realm: string;
  age: number;
  base_battle_strength: number;
  is_current: boolean;
}

export interface PlayerOnboardingOpeningChoiceDTO {
  id: string;
  is_selected: boolean;
  can_select: boolean;
}

export interface PlayerOnboardingDTO {
  viewer_id: string;
  viewer_display_name?: string;
  claimed_seat_id?: string | null;
  owned_sect_id?: number | null;
  owned_sect_name?: string | null;
  main_avatar_id?: string | null;
  main_avatar_name?: string | null;
  opening_choice_id?: string | null;
  opening_choice_applied_month?: number | null;
  intervention_points: number;
  intervention_points_max: number;
  recommended_step: 'claim_sect' | 'set_main_avatar' | 'choose_opening' | 'ready';
  ready: boolean;
  claimable_sects: PlayerOnboardingSectDTO[];
  main_avatar_candidates: PlayerOnboardingAvatarDTO[];
  opening_choices: PlayerOnboardingOpeningChoiceDTO[];
}

export interface InitStatusDTO {
  status: 'idle' | 'pending' | 'in_progress' | 'ready' | 'error';
  phase: number;
  phase_name: string;
  progress: number;
  elapsed_seconds: number;
  error: string | null;
  version?: string;
  llm_check_failed: boolean;
  llm_error_message: string;
  active_room_id?: string;
  room_ids?: string[];
  room_count?: number;
  active_room_summary?: RoomSummaryDTO | null;
  room_summaries?: RoomSummaryDTO[];
  active_controller_id?: string;
  player_control_seat_ids?: string[];
  player_control_seat_count?: number;
  player_control_seats?: Array<{
    id: string;
    holder_id?: string | null;
    holder_display_name?: string;
    owned_sect_id?: number | null;
    main_avatar_id?: string | null;
    is_active?: boolean;
  }>;
  player_profiles?: PlayerProfileDTO[];
  viewer_profile?: PlayerProfileDTO | null;
  player_onboarding?: PlayerOnboardingDTO | null;
}

export interface RoomSummaryDTO {
  id: string;
  access_mode: 'open' | 'private' | string;
  plan_id?: string;
  requested_plan_id?: string;
  commercial_profile?: string;
  price_vnd?: number;
  billing_cycle_days?: number;
  member_limit?: number;
  member_slots_remaining?: number | null;
  entitled_plan_id?: string | null;
  max_selectable_plan_id?: string | null;
  billing_status?: 'trial' | 'active' | 'grace' | 'expired' | string | null;
  billing_period_end_at?: string | null;
  billing_grace_until_at?: string | null;
  billing_deadline_at?: string | null;
  billing_days_remaining?: number | null;
  billing_renewal_recommended?: boolean;
  billing_renewal_stage?: string | null;
  plan_locked_by_billing?: boolean;
  sellable_plan_offers?: RoomPlanOfferDTO[];
  pending_payment_order?: RoomPaymentOrderDTO | null;
  last_paid_order?: RoomPaymentOrderDTO | null;
  payment_events?: RoomPaymentEventDTO[];
  last_payment_ref?: string | null;
  last_payment_amount_vnd?: number | null;
  last_payment_confirmed_at?: string | null;
  owner_viewer_id?: string | null;
  member_viewer_ids?: string[];
  member_count?: number;
  invite_code?: string | null;
  viewer_has_access?: boolean;
  viewer_is_owner?: boolean;
  is_active?: boolean;
  status?: string;
}

export interface RoomPlanOfferDTO {
  plan_id: string;
  commercial_profile: string;
  member_limit: number;
  price_vnd: number;
  billing_cycle_days: number;
  sellable: boolean;
}

export interface RoomPaymentOrderDTO {
  order_id: string;
  room_id?: string;
  target_plan_id: string;
  amount_vnd: number;
  billing_cycle_days: number;
  commercial_profile?: string;
  status: string;
  created_at: string;
  transfer_note?: string;
  provider?: string;
  payment_ref?: string;
  settled_amount_vnd?: number;
  paid_at?: string;
}

export interface RoomPaymentEventDTO {
  timestamp: string;
  event_type: string;
  source: string;
  status: string;
  room_id?: string | null;
  order_id?: string | null;
  payment_ref?: string | null;
  amount_vnd?: number | null;
  target_plan_id?: string | null;
  note?: string | null;
}

export interface PlayerProfileDTO {
  viewer_id: string;
  display_name: string;
  joined_month: number;
  last_seen_month: number;
  controller_id?: string | null;
  owned_sect_id?: number | null;
  main_avatar_id?: string | null;
  is_active_controller?: boolean;
}

export interface RankingAvatarDTO {
  id: string;
  name: string;
  sect: string;
  sect_id?: string;
  realm: string;
  stage: string;
  power: number;
}

export interface RankingSectDTO {
  id: string;
  name: string;
  alignment: string;
  member_count: number;
  total_power: number;
}

export interface TournamentSummaryDTO {
  next_year: number;
  heaven_first?: { id: string; name: string };
  earth_first?: { id: string; name: string };
  human_first?: { id: string; name: string };
}

export interface RankingsDTO {
  heaven: RankingAvatarDTO[];
  earth: RankingAvatarDTO[];
  human: RankingAvatarDTO[];
  sect: RankingSectDTO[];
  tournament?: TournamentSummaryDTO;
}

// --- Sect Relations ---

export interface SectRelationDTO {
  sect_a_id: number;
  sect_a_name: string;
  sect_b_id: number;
  sect_b_name: string;
  value: number;        // -100 ~ 100
  diplomacy_status: 'war' | 'peace' | string;
  diplomacy_duration_months: number;
  reason_breakdown: Array<{
    reason: string;     // 枚举字符串，如 ALIGNMENT_OPPOSITE
    delta: number;      // 本事由对关系值的增减
    meta?: Record<string, unknown>;
  }>;
}

export interface SectRelationsResponseDTO {
  relations: SectRelationDTO[];
}

export interface SectTerritorySummaryDTO {
  id: number;
  name: string;
  color: string;
  influence_radius: number;
  is_active: boolean;
  owned_tiles: Array<{
    x: number;
    y: number;
  }>;
  boundary_edges: Array<{
    x: number;
    y: number;
    side: 'left' | 'right' | 'top' | 'bottom' | string;
  }>;
}

export interface SectTerritoriesResponseDTO {
  sects: SectTerritorySummaryDTO[];
}

export interface TrackedMortalDTO {
  id: string;
  name: string;
  gender: string;
  age: number;
  born_region_id: number;
  born_region_name: string;
  parents: string[];
  is_awakening_candidate: boolean;
}

export interface MortalCityOverviewDTO {
  id: number;
  name: string;
  population: number;
  population_capacity: number;
  natural_growth: number;
}

export interface MortalOverviewResponseDTO {
  summary: {
    total_population: number;
    total_population_capacity: number;
    total_natural_growth: number;
    tracked_mortal_count: number;
    awakening_candidate_count: number;
  };
  cities: MortalCityOverviewDTO[];
  tracked_mortals: TrackedMortalDTO[];
}

export interface DynastyOverviewResponseDTO {
  name: string;
  title: string;
  royal_surname: string;
  royal_house_name: string;
  desc: string;
  effect_desc: string;
  style_tag: string;
  official_preference_label: string;
  is_low_magic: boolean;
  current_emperor?: {
    name: string;
    surname: string;
    given_name: string;
    age: number;
    max_age: number;
    is_mortal: boolean;
  } | null;
}

export interface DynastyOfficialDTO {
  id: string;
  name: string;
  realm: string;
  official_rank_key: string;
  official_rank_name: string;
  court_reputation: number;
  sect_name: string;
}

export interface DynastyDetailResponseDTO {
  overview: DynastyOverviewResponseDTO;
  summary: {
    official_count: number;
    top_official_rank_name: string;
  };
  officials: DynastyOfficialDTO[];
}

// --- Deceased Characters ---

export interface DeceasedRecordDTO {
  id: string;
  name: string;
  gender: string;
  age_at_death: number;
  realm_at_death: string;
  stage_at_death: string;
  death_reason: string;
  death_time: number;
  sect_name_at_death: string;
  alignment_at_death: string;
  backstory: string | null;
  custom_pic_id: number | null;
}

export interface DeceasedListResponseDTO {
  deceased: DeceasedRecordDTO[];
}

export interface AvatarOverviewSummaryDTO {
  total_count: number;
  alive_count: number;
  dead_count: number;
  sect_member_count: number;
  rogue_count: number;
}

export interface AvatarRealmDistributionItemDTO {
  realm: string;
  count: number;
}

export interface AvatarOverviewResponseDTO {
  summary: AvatarOverviewSummaryDTO;
  realm_distribution: AvatarRealmDistributionItemDTO[];
}

export type ToastLevel = 'error' | 'warning' | 'success' | 'info' | string;
export type AppLanguage = AppLocale | string;
export type ToastRenderParam = string | number | boolean | null;

export interface ToastSocketMessage {
  type: 'toast';
  room_id?: string;
  level: ToastLevel;
  message: string;
  language?: AppLanguage;
  render_key?: string;
  render_params?: Record<string, ToastRenderParam>;
}

export interface LLMConfigRequiredSocketMessage {
  type: 'llm_config_required';
  room_id?: string;
  error?: string;
}

export interface GameReinitializedSocketMessage {
  type: 'game_reinitialized';
  room_id?: string;
  message?: string;
}

export interface PongSocketMessage {
  type: 'pong';
}

export type SocketMessageDTO =
  | TickPayloadDTO
  | ToastSocketMessage
  | LLMConfigRequiredSocketMessage
  | GameReinitializedSocketMessage;

export type SocketServerMessageDTO = SocketMessageDTO | PongSocketMessage;
