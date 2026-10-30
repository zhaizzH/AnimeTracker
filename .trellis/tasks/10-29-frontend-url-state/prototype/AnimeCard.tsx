// 原型专用卡片：不依赖外网图片，封面用色块 + 标题。
import type { Anime } from './data';

export function AnimeCard({ anime, highlight }: { anime: Anime; highlight?: boolean }) {
  return (
    <div
      className={
        'rounded-xl border bg-card p-2.5 transition hover:-translate-y-1 hover:border-ring' +
        (highlight ? ' ring-2 ring-ring ring-offset-2 ring-offset-background' : '')
      }
    >
      <div
        className="flex aspect-[3/4] items-end justify-center rounded-lg p-2 text-center text-[11px] leading-tight font-medium text-white/95 break-all"
        style={{
          background: `linear-gradient(160deg, hsl(${anime.hue} 55% 62%), hsl(${(anime.hue + 40) % 360} 45% 38%))`,
        }}
      >
        {anime.title}
      </div>
      <div className="mt-2 truncate text-sm">{anime.title}</div>
      <div className="text-xs text-muted-foreground">
        {anime.score.toFixed(1)} 分 · {anime.eps} 集
      </div>
    </div>
  );
}
