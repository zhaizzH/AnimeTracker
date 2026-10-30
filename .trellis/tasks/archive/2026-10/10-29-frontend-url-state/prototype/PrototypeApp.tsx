// 原型主入口：全部状态在内存，不发任何网络请求。
import { useEffect, useMemo, useRef, useState } from 'react';
import { RotateCcwIcon, SparklesIcon } from 'lucide-react';
import { PrototypeHeader } from './PrototypeHeader';
import { AnimeIndexPage, type Filters } from './AnimeIndexPage';
import { CollectionsPage } from './CollectionsPage';
import { AgentFloat, type Msg } from './AgentFloat';
import { VariantSwitcher, type Variant } from './VariantSwitcher';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ALL, ANIME, ANIME_2022, COLLECTIONS, TABS, WANT_ADDITION } from './data';
import type { Anime } from './data';

const INITIAL_FILTERS: Filters = { keyword: '', year: ALL, weekday: ALL, sort: 'score', order: 'desc' };
const PRINT_2022 = '给我看 2022 年的番';
const COMPOSITE = '把《孤独摇滚》加入想看，然后打开我的收藏';

let uid = 1;
const nextId = () => uid++;

export default function App() {
  const [variant, setVariant] = useState<Variant>('v1');
  const [view, setView] = useState<'anime' | 'collections'>('anime');
  const [filters, setFilters] = useState<Filters>(INITIAL_FILTERS);
  const [collectionTab, setCollectionTab] = useState('want');
  const [wantExtra, setWantExtra] = useState<Anime[]>([]);
  const [highlightIds, setHighlightIds] = useState<number[]>([]);

  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [pending, setPending] = useState(false);
  const [floatOpen, setFloatOpen] = useState(true);
  const [badge, setBadge] = useState(0);
  // 窄屏形态：真实视口 <= 767px 自动生效，也可用底部按钮手动覆盖（桌面里看手机效果）。
  const [isSmall, setIsSmall] = useState(() => window.matchMedia('(max-width: 767px)').matches);
  const [narrowOverride, setNarrowOverride] = useState<boolean | null>(null);
  const narrow = narrowOverride ?? isSmall;

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 767px)');
    const sync = () => setIsSmall(mq.matches);
    mq.addEventListener('change', sync);
    return () => mq.removeEventListener('change', sync);
  }, []);

  const [toast, setToast] = useState<{ id: number; text: string; leaving: boolean } | null>(null);
  const toastTimers = useRef<number[]>([]);

  const items: Anime[] = useMemo(() => {
    const base = filters.year === '2022' ? ANIME_2022 : ANIME;
    if (filters.weekday === ALL) return base;
    const name = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][Number(filters.weekday)];
    return base.filter((a) => a.weekday === name);
  }, [filters.year, filters.weekday]);

  const collectionItems = useMemo(
    () => (collectionTab === 'want' ? [...wantExtra, ...COLLECTIONS.want] : COLLECTIONS[collectionTab] ?? []),
    [collectionTab, wantExtra],
  );

  const counts = useMemo(
    () => ({
      want: COLLECTIONS.want.length + wantExtra.length,
      watched: COLLECTIONS.watched.length,
      watching: COLLECTIONS.watching.length,
      paused: COLLECTIONS.paused.length,
      dropped: COLLECTIONS.dropped.length,
    }),
    [wantExtra.length],
  );

  const url = useMemo(() => {
    if (view === 'collections') return `/my-collections?tab=${collectionTab}&page=1`;
    const p = new URLSearchParams();
    if (filters.year !== ALL) p.set('year', filters.year);
    if (filters.weekday !== ALL) p.set('weekday', filters.weekday);
    if (filters.sort !== 'score') p.set('sort', filters.sort);
    if (filters.order !== 'desc') p.set('order', filters.order);
    p.set('page', '1');
    const qs = p.toString();
    return `/anime${qs ? `?${qs}` : ''}`;
  }, [view, collectionTab, filters]);

  const push = (m: Msg) => setMessages((prev) => [...prev, m]);
  const patch = (id: number, next: Partial<Msg>) =>
    setMessages((prev) => prev.map((m) => (m.id === id ? ({ ...m, ...next } as Msg) : m)));

  const showToast = (text: string) => {
    toastTimers.current.forEach(clearTimeout);
    const id = nextId();
    setToast({ id, text, leaving: false });
    toastTimers.current = [
      window.setTimeout(() => setToast((t) => (t && t.id === id ? { ...t, leaving: true } : t)), 2700),
      window.setTimeout(() => setToast((t) => (t && t.id === id ? null : t)), 3000),
    ];
  };

  // 导航反馈：三套变体的唯一差异点。
  const navigationFeedback = (label: string) => {
    if (variant === 'v2') {
      showToast(`已跳转到「${label}」`);
      return;
    }
    if (variant === 'v3') {
      setFloatOpen(false);
      setBadge((b) => b + 1);
      return;
    }
    push({ id: nextId(), kind: 'system', text: `已跳转到「${label}」` });
  };

  const runTool = (text: string, doneText: string, after: () => void) => {
    setPending(true);
    const toolId = nextId();
    push({ id: toolId, kind: 'tool', text, running: true });
    window.setTimeout(() => {
      patch(toolId, { text: doneText, running: false });
      after();
      setPending(false);
    }, 800);
  };

  const goAnime2022 = () => {
    setView('anime');
    setFilters({ ...INITIAL_FILTERS, year: '2022' });
    setHighlightIds(ANIME_2022.slice(0, 3).map((a) => a.id));
    navigationFeedback('番剧索引 · 2022 年');
  };

  const submit = (override?: string) => {
    const text = (override ?? input).trim();
    if (!text || pending) return;
    setInput('');
    push({ id: nextId(), kind: 'user', text });
    if (text.includes('2022')) {
      runTool('正在检索番剧…', '已检索到 8 部 2022 年的番剧', goAnime2022);
    } else if (text.includes('想看') || text.includes('收藏')) {
      runTool('正在准备写入操作…', '已生成操作预览，等待确认', () =>
        push({
          id: nextId(),
          kind: 'preview',
          title: '将加入想看：《孤独摇滚》',
          body: '确认执行吗？确认后才会写入并跳转到我的收藏。',
        }),
      );
    } else {
      runTool('正在理解指令…', '未匹配到可执行的界面操作', () =>
        push({ id: nextId(), kind: 'assistant', text: '原型只演示「看 2022 年的番」和「加入想看 + 打开收藏」两条指令。' }),
      );
    }
  };

  const confirmPreview = (id: number) => {
    patch(id, { resolved: 'confirmed' });
    runTool('正在加入想看…', '《孤独摇滚》已加入想看', () => {
      setWantExtra((prev) => (prev.some((a) => a.id === WANT_ADDITION.id) ? prev : [WANT_ADDITION, ...prev]));
      setHighlightIds([WANT_ADDITION.id]);
      setCollectionTab('want');
      setView('collections');
      navigationFeedback('我的收藏 · 想看');
    });
  };

  const cancelPreview = (id: number) => {
    patch(id, { resolved: 'cancelled' });
    push({ id: nextId(), kind: 'assistant', text: '已取消，什么都没改。' });
  };

  const reset = () => {
    toastTimers.current.forEach(clearTimeout);
    setToast(null);
    setView('anime');
    setFilters(INITIAL_FILTERS);
    setCollectionTab('want');
    setWantExtra([]);
    setHighlightIds([]);
    setMessages([]);
    setInput('');
    setPending(false);
    setFloatOpen(true);
    setBadge(0);
    setNarrowOverride(false);
  };

  const chooseVariant = (v: Variant) => {
    setVariant(v);
    if (v === 'v3') {
      setNarrowOverride(true);
      setFloatOpen(false);
      setBadge(1);
    } else {
      // 保留当前窄屏开关，方便同屏对比 V1/V2 在窄屏下的表现
      setFloatOpen(true);
      setBadge(0);
    }
  };

  const page = (
    <>
      {/* V2 的页面顶部 toast（放进 page，手机外框里才会相对机身定位） */}
      {toast && variant === 'v2' && (
        <div
          className={
            'fixed top-4 right-4 z-[60] flex w-[19rem] max-w-[calc(100%-2rem)] items-start gap-2 rounded-xl border bg-background p-3 shadow-lg transition-opacity duration-300 animate-in fade-in slide-in-from-top-2 ' +
            (toast.leaving ? 'opacity-0' : 'opacity-100')
          }
          role="status"
        >
          <SparklesIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <p className="text-sm">{toast.text}</p>
          <button
            type="button"
            aria-label="关闭提示"
            className="ml-auto text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setToast(null)}
          >
            ✕
          </button>
        </div>
      )}
      <PrototypeHeader view={view} compact={narrow} onNavigate={(v) => setView(v)} />
      {view === 'anime' ? (
        <AnimeIndexPage filters={filters} items={items} onFiltersChange={setFilters} highlightIds={highlightIds} />
      ) : (
        <CollectionsPage
          tab={collectionTab}
          items={collectionItems}
          counts={counts}
          onTabChange={setCollectionTab}
          highlightIds={highlightIds}
        />
      )}
      <div className="h-24" />
    </>
  );

  const float = (inPhone: boolean) => (
    <AgentFloat
      open={floatOpen}
      narrow={inPhone}
      messages={messages}
      input={input}
      pending={pending}
      badge={badge}
      onInputChange={setInput}
      onSubmit={() => submit()}
      onToggle={() => {
        setFloatOpen((o) => !o);
        setBadge(0);
      }}
      onClose={() => setFloatOpen(false)}
      onConfirm={confirmPreview}
      onCancel={cancelPreview}
      onDemo={(text) => submit(text)}
    />
  );

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-background text-foreground">
      {narrow && !isSmall ? (
        <div className="flex min-h-screen items-start justify-center gap-6 px-4 py-6">
          {/* 手机外框：[transform:translateZ(0)] 让它成为 fixed 后代的包含块，浮层的 right/bottom 相对机身而非真实视口 */}
          <div className="relative h-[760px] w-[375px] shrink-0 overflow-hidden rounded-[2rem] border-4 border-foreground/20 bg-background shadow-2xl [transform:translateZ(0)]">
            <div className="h-full overflow-y-auto">{page}</div>
            {float(true)}
          </div>
          <div className="mt-4 hidden w-[16rem] text-sm text-muted-foreground lg:block">
            <p className="font-medium text-foreground">模拟窄屏 · 375px</p>
            <p className="mt-2 leading-relaxed">
              浮层宽 327px，占 87% 屏宽。V3 下 agent 导航后浮层自动收起为带角标的 Bot 气泡，让新页面完整可见；点气泡可重新展开。
            </p>
            <p className="mt-3 leading-relaxed">输入「给我看 2022 年的番」看收起效果。</p>
          </div>
        </div>
      ) : (
        <div className="relative">
          {page}
          {float(narrow)}
        </div>
      )}

      <VariantSwitcher
        variant={variant}
        url={url}
        busy={pending}
        narrow={narrow}
        onVariant={chooseVariant}
        onToggleNarrow={() => {
          const next = !narrow;
          setNarrowOverride(next);
          if (next && variant === 'v3') {
            setFloatOpen(false);
            setBadge((b) => (b > 0 ? b : 1));
          } else if (!next) {
            setFloatOpen(true);
            setBadge(0);
          }
        }}
        onReset={reset}
      />
      </div>
    </TooltipProvider>
  );
}
