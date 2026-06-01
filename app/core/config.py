# -*- coding: utf-8 -*-

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

# load_dotenv 的作用：
# 把 .env 文件里的 KEY=VALUE 加载到当前 Python 进程的环境变量中。
# 这样业务代码就不用直接写死 API Key、模型名、base_url 等配置。
load_dotenv(ENV_FILE)


def _get_bool(name: str, default: bool = False) -> bool:
    """
    从环境变量中读取布尔值。

    环境变量本质上都是字符串，所以 "true" / "false" 需要我们自己转成 bool。
    """
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_float(name: str, default: float) -> float:
    """
    从环境变量中读取浮点数。

    timeout 这类配置不能一直当字符串用，否则后面传给 HTTP 客户端会出问题。
    """
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default

    try:
        result = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} 必须是数字，例如 30") from exc

    if result <= 0:
        raise ValueError(f"{name} 必须大于 0")

    return result


@dataclass(frozen=True)
class Settings:
    """
    项目配置对象。

    工程意义：
    业务代码不要到处 os.getenv，而是统一从 Settings 读取配置。
    这样以后新增供应商、改模型名、改超时时间，只需要改配置层。
    """

    app_env: str
    use_mock_llm: bool
    enable_mock_fallback: bool
    llm_provider: str
    llm_api_key: str | None
    llm_base_url: str
    llm_model_name: str
    llm_timeout: float

    def safe_dict(self) -> dict:
        """
        返回可展示的配置。

        注意：这里故意不返回真实 API Key，避免健康检查接口或日志泄露密钥。
        """
        return {
            "app_env": self.app_env,
            "use_mock_llm": self.use_mock_llm,
            "enable_mock_fallback": self.enable_mock_fallback,
            "llm_provider": self.llm_provider,
            "llm_base_url": self.llm_base_url,
            "llm_model_name": self.llm_model_name,
            "llm_timeout": self.llm_timeout,
            "has_api_key": bool(self.llm_api_key),
        }


@lru_cache
def get_settings() -> Settings:
    """
    读取项目配置。

    lru_cache 的作用：
    第一次调用时读取 .env，后面复用同一个 Settings 对象。
    配置通常不需要每次请求都重新读取文件，这样更稳定也更省资源。
    """
    use_mock_llm = _get_bool("USE_MOCK_LLM", default=True)
    api_key = os.getenv("LLM_API_KEY") or None

    if not use_mock_llm and not api_key:
        raise ValueError("关闭 mock 后必须配置 LLM_API_KEY，否则无法调用真实模型")

    return Settings(
        app_env=os.getenv("APP_ENV", "dev"),
        use_mock_llm=use_mock_llm,
        enable_mock_fallback=_get_bool("ENABLE_MOCK_FALLBACK", default=False),
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        llm_api_key=api_key,
        llm_base_url=os.getenv("LLM_BASE_URL", "https://api.example.com/v1"),
        llm_model_name=os.getenv("LLM_MODEL_NAME", "mock-chat-model"),
        llm_timeout=_get_float("LLM_TIMEOUT", default=30),
    )
