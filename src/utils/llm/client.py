"""LLM 客户端核心调用逻辑"""

import json
import urllib.request
import urllib.error
import asyncio
from pathlib import Path
from typing import Optional

from src.config import get_settings_service
from src.run.log import log_llm_call
from src.utils.config import CONFIG
from .config import (
    LLMMode,
    LLMConfig,
    get_commercial_profile_name,
    get_task_mode,
    should_execute_task,
)
from .parser import parse_json
from .prompt import build_prompt, load_template
from .exceptions import LLMError, ParseError

# 模块级信号量，懒加载
_SEMAPHORE: Optional[asyncio.Semaphore] = None
_SEMAPHORE_LIMIT: Optional[int] = None


def _get_semaphore() -> asyncio.Semaphore:
    global _SEMAPHORE, _SEMAPHORE_LIMIT
    if _SEMAPHORE is None:
        limit = get_settings_service().get_llm_runtime_config()[0].max_concurrent_requests
        _SEMAPHORE = asyncio.Semaphore(limit)
        _SEMAPHORE_LIMIT = limit
        return _SEMAPHORE

    limit = get_settings_service().get_llm_runtime_config()[0].max_concurrent_requests
    if _SEMAPHORE_LIMIT != limit:
        _SEMAPHORE = asyncio.Semaphore(limit)
        _SEMAPHORE_LIMIT = limit
    return _SEMAPHORE


def _call_openai(config: LLMConfig, prompt: str) -> str:
    """使用原生 urllib 调用 (OpenAI 兼容接口)"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}",
        "User-Agent": "CultivationWorldSimulator/1.0"
    }
    data = {
        "model": config.model_name,
        "messages": [{"role": "user", "content": prompt}]
    }

    url = config.base_url
    if not url:
        raise ValueError("Base URL is required for requests mode (OpenAI Compatible)")

    # URL 规范化处理：确保指向 chat/completions
    if "chat/completions" not in url:
        url = url.rstrip("/")
        url = f"{url}/chat/completions"

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP_{e.code}::{error_body}")
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        reason = getattr(e, "reason", str(e))
        raise Exception(f"NETWORK_ERROR::{reason}")
    except Exception as e:
        if str(e).startswith(("HTTP_", "NETWORK_ERROR::")):
            raise
        raise Exception(f"UNKNOWN_ERROR::{str(e)}")


def _call_anthropic(config: LLMConfig, prompt: str) -> str:
    """使用原生 urllib 调用 (Anthropic 原生接口)"""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": config.api_key,
        "anthropic-version": "2023-06-01",
        "User-Agent": "CultivationWorldSimulator/1.0"
    }
    data = {
        "model": config.model_name,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}]
    }

    url = config.base_url
    if not url:
        raise ValueError("Base URL is required for Anthropic API")

    # URL 规范化处理：确保指向 /v1/messages
    if "/messages" not in url:
        url = url.rstrip("/")
        if not url.endswith("/v1"):
            url = f"{url}/v1"
        url = f"{url}/messages"

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
        # Anthropic 响应格式: {"content": [{"type": "text", "text": "..."}]}
        for block in result.get("content", []):
            if block.get("type") == "text":
                return block["text"]
        raise Exception("UNKNOWN_ERROR::Anthropic 响应中未找到 text 内容")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP_{e.code}::{error_body}")
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        reason = getattr(e, "reason", str(e))
        raise Exception(f"NETWORK_ERROR::{reason}")
    except Exception as e:
        if str(e).startswith(("HTTP_", "NETWORK_ERROR::", "UNKNOWN_ERROR::")):
            raise
        raise Exception(f"UNKNOWN_ERROR::{str(e)}")


def _call_with_requests(config: LLMConfig, prompt: str) -> str:
    """根据 api_format 分发到对应的调用实现"""
    if config.api_format == "anthropic":
        return _call_anthropic(config, prompt)
    return _call_openai(config, prompt)


async def call_llm(
    prompt: str,
    mode: LLMMode = LLMMode.NORMAL,
    additional_info: dict | None = None,
) -> str:
    """
    基础 LLM 调用，自动控制并发
    使用 urllib 直接调用 OpenAI 兼容接口
    """
    config = LLMConfig.from_mode(mode)
    semaphore = _get_semaphore()
    
    async with semaphore:
        result = await asyncio.to_thread(_call_with_requests, config, prompt)
    
    log_llm_call(config.model_name, prompt, result, additional_info=additional_info)
    return result


async def call_llm_json(
    prompt: str,
    mode: LLMMode = LLMMode.NORMAL,
    max_retries: int | None = None,
    additional_info: dict | None = None,
) -> dict:
    """调用 LLM 并解析为 JSON，带重试"""
    if max_retries is None:
        max_retries = int(getattr(CONFIG.ai, "max_parse_retries", 0))
    
    last_error: ParseError | None = None
    for attempt in range(max_retries + 1):
        response = await call_llm(prompt, mode, additional_info=additional_info)
        try:
            return parse_json(response)
        except ParseError as e:
            last_error = e
            if attempt < max_retries:
                continue
            raise LLMError(f"解析失败（重试 {max_retries} 次后）", cause=last_error) from last_error
    
    # This should never be reached, but satisfies type checker.
    raise LLMError("未知错误")


async def call_llm_with_template(
    template_path: Path | str,
    infos: dict,
    mode: LLMMode = LLMMode.NORMAL,
    max_retries: int | None = None,
    additional_info: dict | None = None,
) -> dict:
    """使用模板调用 LLM"""
    template = load_template(template_path)
    prompt = build_prompt(template, infos)
    return await call_llm_json(prompt, mode, max_retries, additional_info=additional_info)


async def call_llm_with_task_name(
    task_name: str,
    template_path: Path | str,
    infos: dict,
    max_retries: int | None = None,
    budget_tracker=None,  # NEW: Optional AIBudgetTracker
) -> dict:
    """
    根据任务名称自动选择 LLM 模式并调用

    Args:
        task_name: 任务名称，用于在 config.yml 中查找对应的模式
        template_path: 模板路径
        infos: 模板参数
        max_retries: 最大重试次数
        budget_tracker: Optional AIBudgetTracker for per-world budget enforcement

    Returns:
        dict: LLM 返回的 JSON 数据
    """
    should_execute, policy, decision = should_execute_task(task_name)
    additional_info = {
        "task_name": task_name,
        "commercial_profile": get_commercial_profile_name(),
        "task_category": policy.category,
        "task_commercial_action": policy.commercial_action,
        "task_policy_decision": decision,
        "task_sample_rate": policy.sample_rate,
    }

    if not should_execute:
        log_llm_call(
            model_name="policy_skip",
            prompt="",
            response="{}",
            duration=0.0,
            additional_info=additional_info,
        )
        # Record fallback in budget tracker if provided
        if budget_tracker is not None:
            budget_tracker.record_fallback(task_name)
        return {}

    # NEW: Check budget before making LLM call
    if budget_tracker is not None:
        allowed, budget_reason = budget_tracker.should_allow_llm_call()
        if not allowed:
            log_llm_call(
                model_name="budget_exhausted",
                prompt="",
                response="{}",
                duration=0.0,
                additional_info={**additional_info, "budget_reason": budget_reason},
            )
            budget_tracker.record_fallback(task_name)
            return {}
        additional_info["budget_status"] = budget_reason

    mode = get_task_mode(task_name)
    additional_info["task_mode"] = mode.value

    result = await call_llm_with_template(
        template_path,
        infos,
        mode,
        max_retries,
        additional_info=additional_info,
    )

    # NEW: Record usage if we got a result (rough estimate based on char count)
    if budget_tracker is not None and result:
        prompt_str = str(infos.get("prompt", ""))
        response_str = str(result)
        # Rough estimate: 1 token ≈ 4 chars for English, ~1.5 for Chinese
        avg_chars_per_token = 2.0
        input_tokens = int(len(prompt_str) / avg_chars_per_token)
        output_tokens = int(len(response_str) / avg_chars_per_token)
        budget_tracker.record_usage(
            task_name=task_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    return result


def test_connectivity(mode: LLMMode = LLMMode.NORMAL, config: Optional[LLMConfig] = None) -> tuple[bool, str]:
    """
    测试 LLM 服务连通性 (同步版本)
    
    Args:
        mode: 测试使用的模式 (NORMAL/FAST)，如果传入 config 则忽略此参数
        config: 直接使用该配置进行测试
        
    Returns:
        tuple[bool, str]: (是否成功, 错误信息)，成功时错误信息为空字符串
    """
    try:
        if config is None:
            config = LLMConfig.from_mode(mode)
            
        _call_with_requests(config, "Hello, this is a connectivity test. Please reply 'OK'.")
        return True, ""
    except Exception as e:
        error_raw = str(e)
        print(f"Connectivity test failed: {error_raw}")
        
        # 1. 尝试解析网络错误
        if error_raw.startswith("NETWORK_ERROR::"):
            reason = error_raw.split("::", 1)[1]
            return False, f"网络连接失败，请检查 Base URL 是否可达或本地代理设置。(底层错误: {reason})"
            
        # 2. 尝试解析 HTTP 错误
        if error_raw.startswith("HTTP_"):
            parts = error_raw.split("::", 1)
            code_str = parts[0].replace("HTTP_", "")
            body_str = parts[1] if len(parts) > 1 else ""
            
            # 尝试从 body 中提取真实的报错字段
            provider_msg = body_str
            try:
                body_json = json.loads(body_str)
                if isinstance(body_json, dict):
                    # 兼容 OpenAI 和大部分厂商的 {"error": {"message": "..."}}
                    if "error" in body_json and isinstance(body_json["error"], dict):
                        provider_msg = body_json["error"].get("message") or body_json["error"].get("msg") or body_str
                    # 兼容 Anthropic 的 {"type": "error", "error": {"type": "...", "message": "..."}}
                    elif body_json.get("type") == "error" and "error" in body_json:
                        err_obj = body_json["error"]
                        if isinstance(err_obj, dict):
                            provider_msg = err_obj.get("message") or body_str
                    # 兼容部分直接 {"message": "..."} 的厂商
                    elif "message" in body_json:
                        provider_msg = body_json["message"]
            except Exception:
                pass # 解析 JSON 失败则保留原字符串
                
            # 截断过长的 HTML/文本报错，防止前端炸版
            if len(provider_msg) > 200:
                provider_msg = provider_msg[:200] + "..."

            # 3. 按照状态码归类
            if code_str == "401":
                return False, f"身份验证失败(401)，请检查 API Key 是否填写正确。服务商返回: {provider_msg}"
            elif code_str == "403":
                return False, f"访问被拒绝(403)，可能是模型未授权或 IP 受限。服务商返回: {provider_msg}"
            elif code_str == "404":
                return False, f"找不到服务(404)，请检查 Base URL 是否正确(通常需要以 /v1 结尾)，或模型名是否存在。服务商返回: {provider_msg}"
            elif code_str == "429":
                return False, f"额度超限或请求频繁(429)，请检查账号余额。服务商返回: {provider_msg}"
            elif code_str.startswith("5"):
                return False, f"服务商内部异常({code_str})，请稍后重试。服务商返回: {provider_msg}"
            else:
                return False, f"请求失败({code_str})。服务商返回: {provider_msg}"
                
        # 3. 未知错误兜底
        return False, f"未知错误: {error_raw}"
