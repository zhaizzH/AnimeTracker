import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminAgentApi, type ModelConfigVO, type ModelConfigViewVO } from '@shared';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toastError, toastSuccess } from '@/lib/toast';

// 后端 ModelConfig 共 5 个字段（见 backend/agent/app/api/schemas/admin_config.py）。
// GET 返回生效值 + 逐字段来源：来源为 default 的字段表单留空、placeholder 显示
// 继承值，提交时不发送，从而不会把 .env 默认值固化进 Redis（后端 set() 是整体替换）。
type ConfigField = 'model' | 'modelRoute' | 'temperature' | 'maxTokens' | 'reasoningEffort';
type ConfigForm = Record<ConfigField, string>;
type AgentConfigData = ModelConfigViewVO;

const CONFIG_FIELDS: ConfigField[] = ['model', 'modelRoute', 'temperature', 'maxTokens', 'reasoningEffort'];
const EMPTY_FORM: ConfigForm = { model: '', modelRoute: '', temperature: '', maxTokens: '', reasoningEffort: '' };

// 空串即「未设置」：不进入提交体，后端整体替换后该键消失，回退继承默认。
// 逐字段显式赋值：TS 对 union key 的写入会把目标类型收窄成交集，用下标赋值无法通过类型检查。
const numOrUndef = (v: string) => (v.trim() === '' ? undefined : Number(v.trim()));
const textOrUndef = (v: string) => (v.trim() === '' ? undefined : v.trim());

/** 提交体只含非空字段，用于撤销未填写字段的覆盖。 */
function toSparseBody(form: ConfigForm): ModelConfigVO {
  const body: ModelConfigVO = {};
  const assign = <K extends ConfigField>(k: K, v: ModelConfigVO[K]) => { if (v !== undefined) body[k] = v; };
  assign('model', textOrUndef(form.model));
  assign('modelRoute', textOrUndef(form.modelRoute));
  assign('temperature', numOrUndef(form.temperature));
  assign('maxTokens', numOrUndef(form.maxTokens));
  assign('reasoningEffort', textOrUndef(form.reasoningEffort));
  return body;
}

/** 从 GET 响应提取「继承默认」字段的值，供 placeholder 展示。 */
function toDefaults(d: AgentConfigData): ModelConfigVO {
  const defs: ModelConfigVO = {};
  const sources = d._sources ?? {};
  const assign = <K extends ConfigField>(k: K, v: ModelConfigVO[K]) => {
    if (v !== null && v !== undefined && sources[k] !== 'override') defs[k] = v;
  };
  assign('model', d.model);
  assign('modelRoute', d.modelRoute);
  assign('temperature', d.temperature);
  assign('maxTokens', d.maxTokens);
  assign('reasoningEffort', d.reasoningEffort);
  return defs;
}

/** override 字段回填 value；default 字段留空。 */
function toForm(d: AgentConfigData): ConfigForm {
  const next = { ...EMPTY_FORM };
  const sources = d._sources ?? {};
  for (const f of CONFIG_FIELDS) {
    const v = d[f];
    if (v !== null && v !== undefined && sources[f] === 'override') next[f] = String(v);
  }
  return next;
}

/**
 * 单个模型配置项。默认来源（未被 Redis 覆盖）的字段 value 留空、以 placeholder
 * 展示继承值，使"留空=继承"在视觉与提交语义上一致；已覆盖字段填实际值。
 */
function ConfigInput({
  id, field, label, cfg, defaults, setCfg, ...inputProps
}: {
  id: string;
  field: ConfigField;
  label: string;
  cfg: ConfigForm;
  defaults: ModelConfigVO;
  setCfg: React.Dispatch<React.SetStateAction<ConfigForm>>;
} & Pick<React.ComponentProps<typeof Input>, 'type' | 'min' | 'max' | 'step'>) {
  const inherited = defaults[field];
  // placeholder 只用于表达「留空即继承默认 X」。已覆盖字段有真实值，无需占位；
  // 且 defaults 中的条目仅来自 default 来源，故无值时即表示该字段已被覆盖。
  const placeholder = inherited === undefined || inherited === null ? undefined : `继承默认 ${String(inherited)}（.env）`;
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        aria-label={field}
        value={cfg[field]}
        placeholder={placeholder}
        onChange={(e) => setCfg((c) => ({ ...c, [field]: e.target.value }))}
        {...inputProps}
      />
    </div>
  );
}

export default function AgentConfig() {
  const qc = useQueryClient();
  const [keys, setKeys] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState('');
  // 区分「加载失败」与「合法的空提示词」：只有成功取回内容才允许保存，
  // 否则 404 时 content 为空串，点保存会把线上提示词覆盖成空。
  const [loaded, setLoaded] = useState(false);
  const [cfg, setCfg] = useState<ConfigForm>(EMPTY_FORM);
  const [cfgError, setCfgError] = useState('');
  const promptsData = useQuery({ queryKey: ['prompts'], queryFn: adminAgentApi.prompts, staleTime: Infinity });
  const modelCfg = useQuery({ queryKey: ['agent-config'], queryFn: adminAgentApi.config, staleTime: Infinity });

  useEffect(() => {
    const raw = promptsData.data;
    if (raw && !keys.length) {
      // 后端返回 PromptVO 数组；adminAgentApi.prompts 的类型即 PromptVO[]，无需再收窄。
      const ks = raw.map((x) => x.promptKey);
      setKeys(ks);
      if (ks[0]) loadDetail(ks[0]);
    }
  }, [promptsData.data]);

  // 模型配置首次到达后回填：仅 override 字段填入 value，default 字段留空由 placeholder 呈现。
  // 仅在尚未初始化时回填，避免后台刷新把用户正在编辑的值覆盖掉。
  const [cfgInitialized, setCfgInitialized] = useState(false);
  const [defaults, setDefaults] = useState<ModelConfigVO>({});
  useEffect(() => {
    const d = modelCfg.data as AgentConfigData | undefined;
    if (d && !cfgInitialized) {
      setCfg(toForm(d));
      setDefaults(toDefaults(d));
      setCfgInitialized(true);
    }
  }, [modelCfg.data, cfgInitialized]);

  // 切换条目时后发的请求可能先返回；用序号丢弃过期响应，保证 content 与 selected 一致。
  const seq = useRef(0);
  const loadDetail = async (k: string) => {
    const my = ++seq.current;
    setSelected(k);
    setContent('');
    setLoaded(false);
    try {
      const d = await adminAgentApi.promptDetail(k);
      if (my !== seq.current) return;
      setContent(String((d as { promptContent?: unknown }).promptContent ?? ''));
      setLoaded(true);
    } catch (e) {
      if (my !== seq.current) return;
      toastError((e as Error).message);
    }
  };
  const savePrompt = useMutation({ mutationFn: () => adminAgentApi.promptUpdate(selected!, { promptContent: content }), onSuccess: () => toastSuccess('提示词已更新'), onError: (e) => toastError((e as Error).message) });
  const resetPrompt = useMutation({ mutationFn: (k: string) => adminAgentApi.promptReset(k), onSuccess: () => { toastSuccess('已重置为默认'); if (selected) loadDetail(selected); }, onError: (e) => toastError((e as Error).message) });
  const saveCfg = useMutation({
    mutationFn: (v: ModelConfigVO) => adminAgentApi.configUpdate(v),
    onSuccess: () => { toastSuccess('配置已更新'); qc.invalidateQueries({ queryKey: ['agent-config'] }); },
    onError: (e) => toastError((e as Error).message),
  });

  const submitCfg = (e: React.FormEvent) => {
    e.preventDefault();
    // temperature 必须落在 [0,2]（对照 antd rules: min 0 / max 2）
    const temp = numOrUndef(cfg.temperature);
    if (temp !== undefined && (temp < 0 || temp > 2)) {
      setCfgError('temperature 必须在 0 到 2 之间');
      return;
    }
    setCfgError('');
    // 只提交非空字段：default 字段不进请求体，故不会被固化进 Redis；
    // 清空已覆盖字段 → 该键消失 → 后端整体替换后回退继承默认。
    saveCfg.mutate(toSparseBody(cfg));
  };

  return (
    <div className="flex flex-col gap-4">
      {/* 选择与编辑同属一个工作区，合并在同一卡片内，免去在两块之间来回找当前的 key */}
      <Card>
        <CardHeader>
          <CardTitle>提示词</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-[minmax(0,220px)_minmax(0,1fr)]">
          <div className="min-w-0">
            {promptsData.isLoading && <p role="status" className="text-sm text-muted-foreground">加载中…</p>}
            {/* 失败与空列表必须分开：否则网络错误会被误读成「暂无提示词」 */}
            {promptsData.isError && (
              <div className="flex flex-col items-start gap-2">
                <p role="alert" className="text-sm text-destructive">提示词加载失败</p>
                <Button size="sm" variant="outline" onClick={() => promptsData.refetch()}>重试</Button>
              </div>
            )}
            {!promptsData.isLoading && !promptsData.isError && keys.length === 0 && (
              <p className="text-sm text-muted-foreground">暂无提示词</p>
            )}
            <ul className="flex flex-col">
              {keys.map((k) => (
                <li
                  key={k}
                  className={`flex items-center gap-2 border-b px-1 py-2 text-sm ${k === selected ? 'bg-muted' : ''}`}
                >
                  {/* min-w-0 + truncate：key 很长时收缩并省略，否则 flex-1 的 min-width:auto
                      会把「重置」顶出列外，溢到右侧编辑区下面造成遮挡 */}
                  <button
                    type="button"
                    aria-current={k === selected ? 'true' : undefined}
                    title={k}
                    className="min-w-0 flex-1 truncate text-left"
                    onClick={() => loadDetail(k)}
                  >
                    {k}
                  </button>
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button size="sm" variant="destructive">重置</Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>重置提示词</AlertDialogTitle>
                        <AlertDialogDescription>重置为默认？当前编辑内容将被丢弃。</AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>取消</AlertDialogCancel>
                        <AlertDialogAction
                          className="bg-destructive text-white hover:bg-destructive/90"
                          onClick={() => resetPrompt.mutate(k)}
                        >
                          确定
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex min-w-0 flex-col gap-3">
            <h3 className="truncate text-sm font-medium" title={selected ?? undefined}>
              {selected ? `编辑：${selected}` : '提示词详情'}
            </h3>
            <Textarea
              // ui/textarea 默认 field-sizing-content：宽度按 cols、高度按内容自适应，
              // 会把卡片越撑越高且宽度压过外层列。这里改回 fixed 并锁定高度，超长提示词走滚动。
              className="field-sizing-fixed h-80 resize-none"
              aria-label="提示词内容"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <Button
              className="self-start"
              disabled={!selected || !loaded || savePrompt.isPending}
              onClick={() => savePrompt.mutate()}
            >
              {savePrompt.isPending ? '保存中…' : '保存提示词'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 模型配置独占下一行 */}
      <Card>
        <CardHeader>
          <CardTitle>模型配置</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" onSubmit={submitCfg}>
            <ConfigInput id="cfg-model" field="model" label="模型" cfg={cfg} defaults={defaults} setCfg={setCfg} />
            <ConfigInput id="cfg-modelRoute" field="modelRoute" label="modelRoute（路由模型）" cfg={cfg} defaults={defaults} setCfg={setCfg} />
            <ConfigInput id="cfg-temperature" field="temperature" label="temperature（0-2）" cfg={cfg} defaults={defaults} setCfg={setCfg}
              type="number" min={0} max={2} step={0.1} />
            <ConfigInput id="cfg-maxTokens" field="maxTokens" label="maxTokens" cfg={cfg} defaults={defaults} setCfg={setCfg}
              type="number" min={1} />
            <ConfigInput id="cfg-reasoningEffort" field="reasoningEffort" label="reasoningEffort（推理强度）" cfg={cfg} defaults={defaults} setCfg={setCfg} />
            {cfgError && <p role="alert" className="text-sm text-destructive sm:col-span-2 lg:col-span-3">{cfgError}</p>}
            <div className="flex items-start gap-3 sm:col-span-2 lg:col-span-3">
              <Button type="submit" disabled={saveCfg.isPending}>保存模型配置</Button>
              <p className="text-xs text-muted-foreground">
                留空表示继承 .env 默认值；清空某个已设置的字段即回退为默认。
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
