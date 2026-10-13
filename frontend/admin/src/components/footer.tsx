import { Link } from 'react-router-dom';
import { GithubIcon } from '@/components/icons/github-icon';
import { Logo } from '@/components/logo';
import { Button } from '@/components/ui/button';

// 取自 @efferd/footer-1，与 client 页脚同骨架；本地化差异：Logo 指向 /dashboard、宽度不设 max-w
// 以契合管理端全宽内容区。nav 段已删除（管理端侧栏常驻，页脚再列一遍导航属冗余）。
export function Footer() {
	return (
		<footer className="*:px-4 *:md:px-6">
			<div className="flex items-center justify-between py-6">
				<Link
					to="/dashboard"
					aria-label="AnimeTracker 管理后台"
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
