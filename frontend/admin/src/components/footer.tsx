import { Link } from 'react-router-dom';
import { ADMIN_NAV_ITEMS } from '@/components/app-sidebar';
import { GithubIcon } from '@/components/icons/github-icon';
import { Logo } from '@/components/logo';
import { Button } from '@/components/ui/button';

// 取自 @efferd/footer-1，与 client 页脚同骨架；本地化差异：导航复用管理端 ADMIN_NAV_ITEMS、
// Logo 指向 /dashboard、宽度不设 max-w 以契合管理端全宽内容区（详见任务 design.md）。
// 管理端导航项让侧栏与页脚链接重名，AdminLayout 测试的链接选择器需用 getAllByRole 取首项。
export function Footer() {
	return (
		<footer className="*:px-4 *:md:px-6">
			<div className="flex flex-col gap-6 py-6">
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-2">
						<Link
							to="/dashboard"
							aria-label="AnimeTracker 管理后台"
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
						{ADMIN_NAV_ITEMS.map((item) => (
							<li key={item.path}>
								<Link className="hover:text-foreground" to={item.path}>
									{item.label}
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
