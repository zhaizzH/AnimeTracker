import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminAgentApi } from '@shared';
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

type ConfigForm = { model?: string; temperature?: string; maxTokens?: string; thinkingBudget?: string };
type AgentConfigData = { model?: string; temperature?: number; maxTokens?: number; thinkingBudget?: number };

const toNumber = (v: string | undefined) => (v === undefined || v === '' ? undefined : Number(v));

export default function AgentConfig() {
  const qc = useQueryClient();
  const [keys, setKeys] = useState<string[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState('');
  const [cfg, setCfg] = useState<ConfigForm>({});
  const [cfgError, setCfgError] = useState('');
  const promptsData = useQuery({ queryKey: ['prompts'], queryFn: adminAgentApi.prompts, staleTime: Infinity });
  const modelCfg = useQuery({ queryKey: ['agent-config'], queryFn: adminAgentApi.config, staleTime: Infinity });

  useEffect(() => {
    const raw = promptsData.data;
    if (raw && !keys.length) {
      // Python 返回结构以实际为准；常见为 { keys: [...] } 或 [{key,...}]；集中在此适配
      const ks = Array.isArray(raw) ? raw.map((x: Record<string, unknown>) => String(x.key)) : Array.isArray((raw as { keys?: unknown }).keys) ? ((raw as { keys: unknown }).keys as string[]) : [];
      setKeys(ks);
      if (ks[0]) loadDetail(ks[0]);
    }
  }, [promptsData.data]);

  // 模型配置首次到达后回填（对照 antd Form 的 initialValues 语义）。
  // 仅在尚未初始化时回填，避免后台刷新把用户正在编辑的值覆盖掉。
  const [cfgInitialized, setCfgInitialized] = useState(false);
  useEffect(() => {
    const d = modelCfg.data as AgentConfigData | undefined;
    if (d && !cfgInitialized) {
      setCfg({
        model: d.model ?? '',
        temperature: d.temperature === undefined ? '' : String(d.temperature),
        maxTokens: d.maxTokens === undefined ? '' : String(d.maxTokens),
        thinkingBudget: d.thinkingBudget === undefined ? '' : String(d.thinkingBudget),
      });
      setCfgInitialized(true);
    }
  }, [modelCfg.data, cfgInitialized]);

  const loadDetail = async (k: string) => { setSelected(k); const d = await adminAgentApi.promptDetail(k).catch(() => ({})); setContent(String((d as { promptContent?: unknown }).promptContent ?? '')); };
  const savePrompt = useMutation({ mutationFn: () => adminAgentApi.promptUpdate(selected!, { promptContent: content }), onSuccess: () => toastSuccess('提示词已更新'), onError: (e) => toastError((e as Error).message) });
  const resetPrompt = useMutation({ mutationFn: (k: string) => adminAgentApi.promptReset(k), onSuccess: () => { toastSuccess('已重置为默认'); if (selected) loadDetail(selected); } });
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
      model: cfg.model || undefined,
      temperature: temp,
      maxTokens: toNumber(cfg.maxTokens),
      thinkingBudget: toNumber(cfg.thinkingBudget),
    });
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,10fr)_minmax(0,14fr)]">
      <Card>
        <CardHeader>
          <CardTitle>提示词</CardTitle>
        </CardHeader>
        <CardContent>
          {promptsData.isLoading && <p role="status" className="text-sm text-muted-foreground">加载中…</p>}
          {!promptsData.isLoading && keys.length === 0 && (
            <p className="text-sm text-muted-foreground">暂无提示词</p>
          )}
          <ul className="flex flex-col">
            {keys.map((k) => (
              <li
                key={k}
                className={`flex items-center justify-between gap-2 border-b px-1 py-2 text-sm ${k === selected ? 'bg-muted' : ''}`}
              >
                <button type="button" className="flex-1 text-left" onClick={() => loadDetail(k)}>
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
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle>{selected ? `编辑：${selected}` : '提示词详情'}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Textarea
              rows={12}
              aria-label="提示词内容"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
            <Button
              className="self-start"
              disabled={!selected || savePrompt.isPending}
              onClick={() => savePrompt.mutate()}
            >
              {savePrompt.isPending ? '保存中…' : '保存提示词'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>模型配置</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-4" onSubmit={submitCfg}>
              <div className="flex flex-col gap-2">
                <Label htmlFor="cfg-model">模型</Label>
                <Input id="cfg-model" aria-label="模型" value={cfg.model ?? ''}
                  onChange={(e) => setCfg((c) => ({ ...c, model: e.target.value }))} />
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
              {cfgError && <p role="alert" className="text-sm text-destructive">{cfgError}</p>}
              <Button type="submit" className="self-start">保存模型配置</Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
