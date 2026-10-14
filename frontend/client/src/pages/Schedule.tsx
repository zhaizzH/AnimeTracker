import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { subjectsApi } from '@shared';
import { SubjectGrid } from '@/components/SubjectGrid';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { cn } from '@/lib/utils';

const QUARTERS = { spring: '春', summer: '夏', autumn: '秋', winter: '冬' } as const;
const QUARTER_KEYS = ['winter', 'spring', 'summer', 'autumn'] as const;
const quarterOf = (d: Date) => QUARTER_KEYS[Math.floor(d.getMonth() / 3)];
const WEEK = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
const weekdayIndex = (w: number) => (w + 6) % 7; // JS getDay() 0=周日 → 周一=0
// 后端 airWeekday/weekday: 0=周日…6=周六；标签页下标 i: 0=周一…6=周日，互转
const tabToWeekday = (i: number) => (i + 1) % 7;

export default function Schedule() {
  const now = new Date();
  const [params, setParams] = useSearchParams();
  const year = Number(params.get('year') ?? now.getFullYear());
  const quarter = params.get('quarter') ?? quarterOf(now);
  const active = params.get('tab') ?? String(weekdayIndex(now.getDay()));
  const patch = (p: Record<string, string>) => setParams({ year: String(year), quarter, tab: active, ...p });

  // 后端按 airWeekday 升序分页、size 上限 100 会截断尾部星期 → 按天查询；仅加载当前查看的星期
  const { data, isLoading } = useQuery({
    queryKey: ['schedule', year, quarter, active],
    queryFn: () => subjectsApi.schedule({ year, quarter, weekday: tabToWeekday(Number(active)), size: 100 }),
  });

  return (
    <div className="mx-auto w-full max-w-[1400px] p-6">
      <div className="mb-4 flex flex-wrap gap-3">
        <Select value={String(year)} onValueChange={(v) => patch({ year: v })}>
          <SelectTrigger className="w-[110px]" aria-label="年份"><SelectValue /></SelectTrigger>
          <SelectContent>
            {[year - 1, year, year + 1].map((y) => <SelectItem key={y} value={String(y)}>{y}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={quarter} onValueChange={(v) => patch({ quarter: v })}>
          <SelectTrigger className="w-[90px]" aria-label="季度"><SelectValue /></SelectTrigger>
          <SelectContent>
            {Object.entries(QUARTERS).map(([v, label]) => <SelectItem key={v} value={v}>{label}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div role="tablist" aria-label="星期" className="mb-4 flex flex-wrap gap-1 border-b">
        {WEEK.map((label, i) => (
          <button
            key={i}
            type="button"
            role="tab"
            aria-selected={String(i) === active}
            className={cn(
              '-mb-px border-b-2 px-4 py-2 text-sm',
              String(i) === active ? 'border-primary font-medium text-foreground' : 'border-transparent text-muted-foreground hover:text-foreground',
            )}
            onClick={() => patch({ tab: String(i) })}
          >
            {label}
          </button>
        ))}
      </div>

      <SubjectGrid
        items={(data?.content ?? []).filter((s) => s.airWeekday === tabToWeekday(Number(active)))}
        loading={isLoading}
      />
    </div>
  );
}
