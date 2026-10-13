import { cn } from '@/lib/utils';

type FullWidthDividerProps = React.ComponentProps<'div'> & {
	contained?: boolean;
	position?: 'top' | 'bottom';
};

/**
 * 全宽/容器内分隔线。逐字移植 efferd `@efferd/full-width-divider`
 * （https://efferd.com/r/new-york/full-width-divider.json），保留两端模式：
 * `contained=false`（默认）为相对视口居中的 full-bleed；`contained=true` 时与父容器同宽。
 * 纯展示、`aria-hidden`，无状态无 hook。
 */
export function FullWidthDivider({
	className,
	contained = false,
	position,
	...props
}: FullWidthDividerProps) {
	return (
		<div
			aria-hidden="true"
			className={cn(
				'pointer-events-none absolute h-px bg-border',
				// full-bleed (default)
				'data-[contained=false]:left-1/2 data-[contained=false]:w-screen data-[contained=false]:-translate-x-1/2',
				// contained
				'data-[contained=true]:inset-x-0 data-[contained=true]:w-full',
				// position
				position && 'data-[position=top]:-top-px data-[position=bottom]:-bottom-px',
				className
			)}
			data-contained={contained}
			data-position={position}
			{...props}
		/>
	);
}
