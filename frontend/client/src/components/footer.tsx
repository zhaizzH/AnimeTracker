import { Link } from 'react-router-dom';
import { GithubIcon } from '@/components/icons/github-icon';
import { Logo } from '@/components/logo';
import { Button } from '@/components/ui/button';

// 取自 @efferd/footer-1（https://efferd.com/r/new-york/footer-1.json），保留上游 DOM 骨架，
// 仅将占位内容本地化：导航换真实路由、社交仅留 GitHub、版权改 AnimeTracker、删除上游署名外链。
// 宽度与顶栏 nav 对齐（同为 max-w-[1400px]），页脚与页头共用同一横向节奏。
const navLinks = [
	{ href: '/', label: '首页' },
	{ href: '/anime', label: '番剧索引' },
	{ href: '/schedule', label: '每周日程' },
];

export function Footer() {
	return (
		<footer className="mx-auto w-full max-w-[1400px] *:px-4 *:md:px-6">
			<div className="flex flex-col gap-6 py-6">
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-2">
						<Link
							to="/"
							aria-label="AnimeTracker 首页"
							className="rounded-md p-1 hover:bg-muted dark:hover:bg-muted/50"
						>
							<Logo className="h-4" />
						</Link>
					</div>
					<div className="flex items-center">
						<Button asChild size="icon" variant="ghost">
							<a aria-label="GitHub" href="https://github.com/zhaizzH" rel="noreferrer" target="_blank">
								<GithubIcon className="size-4" />
							</a>
						</Button>
					</div>
				</div>

				<nav>
					<ul className="flex flex-wrap gap-4 font-medium text-muted-foreground text-sm md:gap-6">
						{navLinks.map((link) => (
							<li key={link.label}>
								<Link className="hover:text-foreground" to={link.href}>
									{link.label}
								</Link>
							</li>
						))}
					</ul>
				</nav>
			</div>

			<div className="flex items-center justify-between gap-4 border-t py-4 text-muted-foreground text-sm">
				<p>&copy; {new Date().getFullYear()} AnimeTracker</p>
			</div>
		</footer>
	);
}
