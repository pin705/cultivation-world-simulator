/**
 * Recap 类型定义
 * 
 * Recap-first gameplay loop - 水墨风格的事件回顾系统
 */

/**
 * Recap 完整响应
 */
export interface RecapResponse {
  /** 时间段文本，如 "Year 5 January - Year 5 March" */
  period_text: string;
  /** 是否有未读的 recap */
  has_unread_recap: boolean;
  /** Action points 状态 */
  action_points: ActionPointsState;
  /** 宗门 recap（如果玩家拥有宗门） */
  sect?: SectRecapSection;
  /** 主要弟子 recap（如果玩家有主要弟子） */
  main_disciple?: DiscipleRecapSection;
  /** 世界事件 recap */
  world: WorldRecapSection;
  /** 机会和建议 */
  opportunities: OpportunitySection;
  /** 总结文本（可选） */
  summary_text?: string;
}

/**
 * Action points 状态
 */
export interface ActionPointsState {
  /** 剩余 points */
  remaining: number;
  /** 总 points */
  total: number;
}

/**
 * 宗门 recap 部分
 */
export interface SectRecapSection {
  /** 宗门 ID */
  sect_id: number;
  /** 宗门名称 */
  sect_name: string;
  /** 状态变化 */
  status_changes: string[];
  /** 成员事件 */
  member_events: string[];
  /** 资源变化 */
  resource_changes: string[];
  /** 威胁 */
  threats: string[];
}

/**
 * 弟子 recap 部分
 */
export interface DiscipleRecapSection {
  /** 角色 ID */
  avatar_id: string;
  /** 姓名 */
  name: string;
  /** 修炼进展 */
  cultivation_progress?: string;
  /** 重要事件 */
  major_events: string[];
  /** 关系变化 */
  relationships: string[];
  /** 当前状态 */
  current_status?: string;
}

/**
 * 世界 recap 部分
 */
export interface WorldRecapSection {
  /** 重大事件 */
  major_events: string[];
  /** 宗门关系变化 */
  sect_relations: string[];
  /** 天地灵机 */
  phenomenon?: string;
  /** 榜单是否变化 */
  rankings_changed: boolean;
}

/**
 * 机会部分
 */
export interface OpportunitySection {
  /** 可用机会 */
  opportunities: string[];
  /** 待决决定 */
  pending_decisions: string[];
  /** 建议行动 */
  suggested_actions: string[];
}

/**
 * 确认 recap 响应
 */
export interface AcknowledgeRecapResponse {
  /** 上次已读 recap 的月份 */
  last_recap_month_stamp: number;
  /** 上次确认的月份 */
  last_acknowledge_month_stamp: number;
  /** Action points 状态 */
  action_points: ActionPointsState;
}

/**
 * 花费 action point 响应
 */
export interface ActionPointResponse {
  /** Action points 状态 */
  action_points: ActionPointsState;
}
