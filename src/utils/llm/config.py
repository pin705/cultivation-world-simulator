"""LLM 配置管理"""

from contextlib import contextmanager
from contextvars import ContextVar
from enum import Enum
from dataclasses import dataclass
import random
from typing import Any

from src.config import get_settings_service
from src.utils.config import CONFIG

_COMMERCIAL_PROFILE_OVERRIDE: ContextVar[str | None] = ContextVar(
    "llm_commercial_profile_override",
    default=None,
)

class LLMMode(str, Enum):
    """LLM 调用模式"""
    NORMAL = "normal"
    FAST = "fast"
    DEFAULT = "default"


@dataclass(frozen=True)
class LLMConfig:
    """LLM 配置数据类"""
    model_name: str
    api_key: str
    base_url: str
    api_format: str = "openai"  # "openai" 或 "anthropic"

    @classmethod
    def from_mode(cls, mode: LLMMode) -> 'LLMConfig':
        """
        根据模式创建配置，从 CONFIG 读取

        Args:
            mode: LLM 调用模式

        Returns:
            LLMConfig: 配置对象
        """
        profile, api_key = get_settings_service().get_llm_runtime_config()
        base_url = profile.base_url

        # 根据模式选择模型
        model_name = ""
        if mode == LLMMode.FAST:
            model_name = profile.fast_model_name
        else:
            # NORMAL or DEFAULT fallback
            model_name = profile.model_name

        return cls(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            api_format=getattr(profile, 'api_format', 'openai')
        )


@dataclass(frozen=True)
class LLMTaskPolicy:
    """单个任务的 LLM 调用策略。"""
    task_name: str
    enabled: bool = True
    sample_rate: float = 1.0
    category: str = "core"
    commercial_action: str = "keep"
    note: str = ""


def get_commercial_profile_name() -> str:
    override = str(_COMMERCIAL_PROFILE_OVERRIDE.get() or "").strip()
    if override:
        return override
    profile, _ = get_settings_service().get_llm_runtime_config()
    return str(getattr(profile, "commercial_profile", "standard") or "standard")


@contextmanager
def use_commercial_profile_override(profile_name: str | None):
    normalized = str(profile_name or "").strip() or None
    token = _COMMERCIAL_PROFILE_OVERRIDE.set(normalized)
    try:
        yield
    finally:
        _COMMERCIAL_PROFILE_OVERRIDE.reset(token)


def _get_config_entry(container: Any, key: str, default: Any = None) -> Any:
    if container is None:
        return default
    if isinstance(container, dict):
        return container.get(key, default)
    try:
        return container[key]
    except (KeyError, TypeError, AttributeError):
        pass
    return getattr(container, key, default)


def _resolve_task_policy_source(task_name: str) -> tuple[Any, Any]:
    raw_policies = getattr(CONFIG.llm, "task_policies", None)
    base_raw = _get_config_entry(raw_policies, task_name)

    profile_name = get_commercial_profile_name()
    commercial_profiles = getattr(CONFIG.llm, "commercial_profiles", None)
    profile_raw = _get_config_entry(commercial_profiles, profile_name)
    profile_policies = _get_config_entry(profile_raw, "task_policies") if profile_raw is not None else None
    override_raw = _get_config_entry(profile_policies, task_name)
    return base_raw, override_raw


def _resolve_task_mode_source(task_name: str) -> Any:
    profile_name = get_commercial_profile_name()
    commercial_profiles = getattr(CONFIG.llm, "commercial_profiles", None)
    profile_raw = _get_config_entry(commercial_profiles, profile_name)
    profile_modes = _get_config_entry(profile_raw, "default_modes") if profile_raw is not None else None
    override_mode = _get_config_entry(profile_modes, task_name)
    if override_mode is not None:
        return override_mode

    default_modes = getattr(CONFIG.llm, "default_modes", None)
    return _get_config_entry(default_modes, task_name)


def get_task_policy(task_name: str) -> LLMTaskPolicy:
    """读取任务级 LLM 策略；未配置时使用保守默认值。"""
    base_raw, override_raw = _resolve_task_policy_source(task_name)
    raw = override_raw if override_raw is not None else base_raw

    if raw is None:
        return LLMTaskPolicy(task_name=task_name)

    enabled = bool(_get_config_entry(override_raw, "enabled", _get_config_entry(base_raw, "enabled", True)))
    sample_rate = float(
        _get_config_entry(override_raw, "sample_rate", _get_config_entry(base_raw, "sample_rate", 1.0))
    )
    sample_rate = max(0.0, min(1.0, sample_rate))
    return LLMTaskPolicy(
        task_name=task_name,
        enabled=enabled,
        sample_rate=sample_rate,
        category=str(_get_config_entry(override_raw, "category", _get_config_entry(base_raw, "category", "core")) or "core"),
        commercial_action=str(
            _get_config_entry(
                override_raw,
                "commercial_action",
                _get_config_entry(base_raw, "commercial_action", "keep"),
            )
            or "keep"
        ),
        note=str(_get_config_entry(override_raw, "note", _get_config_entry(base_raw, "note", "")) or ""),
    )


def should_execute_task(task_name: str) -> tuple[bool, LLMTaskPolicy, str]:
    """
    根据任务策略判断本次是否执行。

    Returns:
        tuple[bool, LLMTaskPolicy, str]:
            - 是否执行
            - 任务策略
            - 决策原因：enabled / disabled / sample_rate_zero / sampled_out
    """
    policy = get_task_policy(task_name)
    if not policy.enabled:
        return False, policy, "disabled"
    if policy.sample_rate <= 0.0:
        return False, policy, "sample_rate_zero"
    if policy.sample_rate < 1.0 and random.random() > policy.sample_rate:
        return False, policy, "sampled_out"
    return True, policy, "enabled"


def get_task_mode(task_name: str) -> LLMMode:
    """
    根据任务名称获取 LLM 模式
    """
    # 从 CONFIG 读取全局模式
    profile, _ = get_settings_service().get_llm_runtime_config()
    global_mode = (profile.mode or "default").lower()
    
    if global_mode == "normal":
        return LLMMode.NORMAL
    elif global_mode == "fast":
        return LLMMode.FAST
    
    # Default 模式：先看 commercial profile override，再看全局 default_modes。
    task_mode = _resolve_task_mode_source(task_name)
    if task_mode:
        task_mode = str(task_mode).lower()
        if task_mode == "fast":
            return LLMMode.FAST
        else:
            return LLMMode.NORMAL
    
    # 如果没有配置，默认返回 NORMAL
    return LLMMode.NORMAL
