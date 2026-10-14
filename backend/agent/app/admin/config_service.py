from app.admin.ports import ModelConfigRepository, PromptRepository
from app.config import Settings, resolve_llm_provider

# 逐字段取值：与 agent_factory.AgentLlmFactory.create() 的解析链逐字对齐，
# 否则管理页回显的值与运行时实际使用的值会不一致。
# 两类语义不可互换：
#   - model/modelRoute 走 `or`：空串视为未设置，回退默认
#   - 其余看键是否存在：0 是 temperature 的合法值，须保留（不得当未设置）
_TRUTHY_FIELDS = ("model", "modelRoute")


class AdminConfigService:
    def __init__(self, model_configs: ModelConfigRepository, prompts: PromptRepository, settings: Settings):
        self._model_configs = model_configs
        self._prompts = prompts
        self._settings = settings

    def list_prompts(self) -> list[dict[str, str]]:
        return [{"promptKey": key, "promptContent": self._prompts.get(key)} for key in self._prompts.list_keys()]

    def get_prompt(self, key: str) -> dict[str, str]:
        self._ensure_prompt_key(key)
        return {"promptKey": key, "promptContent": self._prompts.get(key)}

    def update_prompt(self, key: str, content: str) -> dict[str, str]:
        self._ensure_prompt_key(key)
        self._prompts.set(key, content)
        return {"promptKey": key, "promptContent": self._prompts.get(key)}

    def reset_prompt(self, key: str) -> dict[str, str]:
        self._ensure_prompt_key(key)
        content = self._prompts.reset(key)
        return {"promptKey": key, "promptContent": content}

    def _defaults(self) -> dict:
        """Settings(.env) 侧的默认值。"""
        resolved = resolve_llm_provider(self._settings)
        return {
            "model": resolved.model,
            "modelRoute": resolved.route_model,
            "temperature": self._settings.llm_temperature,
            "maxTokens": self._settings.llm_max_tokens,
            "thinkingBudget": self._settings.llm_thinking_budget,
            "reasoningEffort": resolved.reasoning_effort,
        }

    def get_effective_config(self) -> dict:
        """生效值 + 逐字段来源。

        Redis 未设置的字段回退 Settings(.env)，来源标 ``default``；
        显式覆盖的标 ``override``。回显值即为运行时实际使用的值。
        """
        runtime = self._model_configs.get() or {}
        defaults = self._defaults()
        effective: dict = {}
        sources: dict = {}
        for field, default in defaults.items():
            # 与工厂对齐：model/modelRoute 用真值判断（空串回退），其余看键是否存在
            has_override = bool(runtime.get(field)) if field in _TRUTHY_FIELDS else field in runtime and runtime[field] is not None
            if has_override:
                effective[field], sources[field] = runtime[field], "override"
            else:
                effective[field], sources[field] = default, "default"
        return {**effective, "_sources": sources}

    def get_model_config(self) -> dict:
        """兼容旧调用：仅 Redis 原始内容。"""
        return self._model_configs.get() or {}

    def update_model_config(self, config: dict) -> dict:
        # 空对象等价于没有修改：整体替换语义下 set({}) 会清空全部覆盖，
        # 而调用方（前端提交空表单）的本意是"没改任何字段"，故直接返回现值不动存储。
        if not config:
            return self.get_effective_config()

        temperature = config.get("temperature")
        if temperature is not None and not 0 <= temperature <= 2:
            raise ValueError("temperature 需在 0~2 之间")
        max_tokens = config.get("maxTokens")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("maxTokens 需为正整数")

        # 整体替换（保持既有语义）：前端只提交非空字段，故提交集即目标覆盖集。
        # 清空某字段 → 它不在提交体 → 替换后该键消失 → 回退继承默认。
        # 不做合并：合并会保留旧值，使"清空单字段"无法撤销覆盖。
        self._model_configs.set(config)
        return self.get_effective_config()

    def _ensure_prompt_key(self, key: str) -> None:
        if key not in self._prompts.list_keys():
            raise KeyError(key)
