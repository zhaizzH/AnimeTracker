import { CalendarDays, ListVideo, Star, Tag, Trophy, type LucideIcon } from 'lucide-react';
import { formatDate } from '@shared';
import { FullWidthDivider } from '@/components/full-width-divider';
import { cn } from '@/lib/utils';

// 客户端对后端 subject type 枚举的映射。放在本组件而非页面：字段拼装已随卡片一并内聚。
const SUBJECT_TYPE_LABEL: Record<number, string> = { 1: '书籍', 2: '动画', 3: '音乐', 4: '游戏', 6: '三次元' };

type InfoRow = { label: string; value: string | number; Icon: LucideIcon };

type Props = {
	rank: number;
	eps: number;
	airDate?: string | null;
	type: number;
	collectionTotal: number;
	className?: string;
};

/**
 * 条目详情页的信息栏，形态取自 efferd `@efferd/contact-1`（卡片网格 + 上下分隔线），
 * 但按本地语义落地：外层 `<dl>`、每张卡片为 `<dt>`（标题）/`<dd>`（值）分组，
 * 不引入上游的 `IconPlaceholder` 与 `font-heading` 区块标题。
 *
 * 占位符区分两种情形：**缺值**（`rank <= 0`、无 `airDate`）显示 `—`；
 * **有值但枚举未映射**（后端新增 type）保留原始码 `未知(n)`，便于发现映射缺口。
 * 分隔线用 `contained`（与卡片网格同宽），因内容列不在视口中心，full-bleed 会横向溢出。
 */
export function SubjectInfoCards({ rank, eps, airDate, type, collectionTotal, className }: Props) {
	const rows: InfoRow[] = [
		{ label: '排名', value: rank > 0 ? rank : '—', Icon: Trophy },
		{ label: '集数', value: eps, Icon: ListVideo },
		{ label: '放送', value: formatDate(airDate), Icon: CalendarDays },
		{ label: '类型', value: SUBJECT_TYPE_LABEL[type] ?? `未知(${type})`, Icon: Tag },
		{ label: '收藏', value: collectionTotal, Icon: Star },
	];

	return (
		<div className={cn('relative', className)}>
			<FullWidthDivider contained position="top" />
			<dl className="grid gap-px overflow-hidden bg-border px-px md:grid-cols-3">
				{rows.map(({ label, value, Icon }) => (
					<div key={label} className="flex items-center gap-3 bg-background p-2 shadow-xs">
						<div
							aria-hidden="true"
							className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-muted/50 [&_svg]:size-4 [&_svg]:text-muted-foreground"
						>
							<Icon />
						</div>
						<div className="flex min-w-0 flex-col gap-y-0.5">
							<dt className="font-heading text-sm">{label}</dt>
							<dd className="break-words text-muted-foreground text-xs">{String(value)}</dd>
						</div>
					</div>
				))}
			</dl>
			<FullWidthDivider contained position="bottom" />
		</div>
	);
}
