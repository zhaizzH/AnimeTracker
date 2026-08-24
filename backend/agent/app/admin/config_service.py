from app.admin.ports import ModelConfigRepository, PromptRepository


class AdminConfigService:
    def __init__(self, model_configs: ModelConfigRepository, prompts: PromptRepository):
        self._model_configs = model_configs
        self._prompts = prompts

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

    def get_model_config(self) -> dict:
        return self._model_configs.get() or {}

    def update_model_config(self, config: dict) -> dict:
        temperature = config.get("temperature")
        if temperature is not None and not 0 <= temperature <= 2:
            raise ValueError("temperature 需在 0~2 之间")
        max_tokens = config.get("maxTokens")
        if max_tokens is not None and max_tokens <= 0:
            raise ValueError("maxTokens 需为正整数")
        self._model_configs.set(config)
        return config

    def _ensure_prompt_key(self, key: str) -> None:
        if key not in self._prompts.list_keys():
            raise KeyError(key)
