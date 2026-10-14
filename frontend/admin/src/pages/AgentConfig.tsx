import { useEffect, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminAgentApi, type ModelConfigVO } from '@shared';
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

// 后端 ModelConfig 共 6 个字段（见 backend/agent/app/api/schemas/admin_config.py）；
// 表单只呈现其中一部分，其余靠 serverCfg 原样带回，避免被整体替换抹掉。
type ConfigForm = { model?: string; modelRoute?: string; temperature?: string; maxTokens?: string; thinkingBudget?: string; reasoningEffort?: string };
type AgentConfigData = ModelConfigVO;

const toNumber = (v: string | undefined) => (v === undefined || v === '' ? undefined : Number(v));
const toText = (v: string | undefined) => (v === undefined || v === '' ? undefined : v);

export default function AgentConfig() {
  const qc = useQueryClient();
  const [keys, setKeys] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState('');
  // 区分「加载失败」与「合法的空提示词」：只有成功取回内容才允许保存，
  // 否则 404 时 content 为空串，点保存会把线上提示词覆盖成空。
  const [loaded, setLoaded] = useState(false);
  const [cfg, setCfg] = useState<ConfigForm>({});
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

  // 模型配置首次到达后回填（对照 antd Form 的 initialValues 语义）。
  // 仅在尚未初始化时回填，避免后台刷新把用户正在编辑的值覆盖掉。
  const [cfgInitialized, setCfgInitialized] = useState(false);
  // GET 的原始对象：提交时作为基底，保全表单未呈现的字段（后端 set() 是整体替换，不是合并）。
  const [serverCfg, setServerCfg] = useState<Record<string, unknown>>({});
  useEffect(() => {
    const d = modelCfg.data as AgentConfigData | undefined;
    if (d && !cfgInitialized) {
      setServerCfg(d as Record<string, unknown>);
      setCfg({
        model: d.model ?? '',
        modelRoute: d.modelRoute ?? '',
        temperature: d.temperature === undefined ? '' : String(d.temperature),
        maxTokens: d.maxTokens === undefined ? '' : String(d.maxTokens),
        thinkingBudget: d.thinkingBudget === undefined ? '' : String(d.thinkingBudget),
        reasoningEffort: d.reasoningEffort ?? '',
      });
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
    mutationFn: (v: Record<string, unknown>) => adminAgentApi.configUpdate(v),
    onSuccess: () => { toastSuccess('配置已更新'); qc.invalidateQueries({ queryKey: ['agent-config'] }); },
    onError: (e) => toastError((e as Error).message),
  });

  const submitCfg = (e: React.FormEvent) => {
    e.preventDefault();
    // temperature 必须落在 [0,2]（对照 antd rules: min 0 / max 2）
    const temp = toNumber(cfg.temperature);
    if (temp !== undefined && (temp < 0 || temp > 2)) {
      setCfgError('temperature 必须在 0 到 2 之间');
      return;
    }
    setCfgError('');
    saveCfg.mutate({
      // 以服务端返回值打底，再覆盖表单字段 —— 后端是整体替换，缺字段即被抹除。
      ...serverCfg,
      model: toText(cfg.model),
      modelRoute: toText(cfg.modelRoute),
      temperature: temp,
      maxTokens: toNumber(cfg.maxTokens),
      thinkingBudget: toNumber(cfg.thinkingBudget),
      reasoningEffort: toText(cfg.reasoningEffort),
    });
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
            <div className="flex flex-col gap-2">
              <Label htmlFor="cfg-model">模型</Label>
              <Input id="cfg-model" aria-label="模型" value={cfg.model ?? ''}
                onChange={(e) => setCfg((c) => ({ ...c, model: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="cfg-modelRoute">modelRoute（路由模型）</Label>
              <Input id="cfg-modelRoute" aria-label="modelRoute" value={cfg.modelRoute ?? ''}
                onChange={(e) => setCfg((c) => ({ ...c, modelRoute: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="cfg-temperature">temperature（0-2）</Label>
              <Input id="cfg-temperature" type="number" min={0} max={2} step={0.1} aria-label="temperature"
                value={cfg.temperature ?? ''}
                onChange={(e) => setCfg((c) => ({ ...c, temperature: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="cfg-maxTokens">maxTokens</Label>
              <Input id="cfg-maxTokens" type="number" min={1} aria-label="maxTokens"
                value={cfg.maxTokens ?? ''}
                onChange={(e) => setCfg((c) => ({ ...c, maxTokens: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="cfg-thinkingBudget">thinkingBudget</Label>
              <Input id="cfg-thinkingBudget" type="number" min={0} aria-label="thinkingBudget"
                value={cfg.thinkingBudget ?? ''}
                onChange={(e) => setCfg((c) => ({ ...c, thinkingBudget: e.target.value }))} />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="cfg-reasoningEffort">reasoningEffort（推理强度）</Label>
              <Input id="cfg-reasoningEffort" aria-label="reasoningEffort" value={cfg.reasoningEffort ?? ''}
                onChange={(e) => setCfg((c) => ({ ...c, reasoningEffort: e.target.value }))} />
            </div>
            {cfgError && <p role="alert" className="text-sm text-destructive sm:col-span-2 lg:col-span-3">{cfgError}</p>}
            <Button type="submit" className="justify-self-start">保存模型配置</Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
