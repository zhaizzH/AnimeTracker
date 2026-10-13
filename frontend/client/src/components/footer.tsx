import { Link } from 'react-router-dom';
import { GithubIcon } from '@/components/icons/github-icon';
import { Logo } from '@/components/logo';
import { Button } from '@/components/ui/button';

// 取自 @efferd/footer-1（https://efferd.com/r/new-york/footer-1.json），保留「Logo + 图标位 / 版权行」
// 骨架，已去除上游 nav 段（与顶栏公开项重复）、署名外链与 href="#" 死链，版权改为 AnimeTracker。
// 宽度与顶栏 nav 对齐（同为 max-w-[1400px]），页脚与页头共用同一横向节奏。
export function Footer() {
	return (
		<footer className="mx-auto w-full max-w-[1400px] *:px-4 *:md:px-6">
			<div className="flex items-center justify-between py-6">
				<Link
					to="/"
					aria-label="AnimeTracker 首页"
					className="rounded-md p-1 hover:bg-muted dark:hover:bg-muted/50"
				>
					<Logo className="h-4" />
				</Link>
				<Button asChild size="icon" variant="ghost">
					<a aria-label="GitHub" href="https://github.com/zhaizzH" rel="noreferrer" target="_blank">
						<GithubIcon className="size-4" />
					</a>
				</Button>
			</div>

			<div className="flex items-center justify-between gap-4 border-t py-4 text-muted-foreground text-sm">
				<p>&copy; {new Date().getFullYear()} AnimeTracker</p>
			</div>
		</footer>
	);
}
