import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { SubjectCard, subjectsApi } from '@shared';
import { CollectionActions } from '@/components/CollectionActions';
import { SubjectInfoCards } from '@/components/subject-info-cards';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

const EP_STATUS_LABEL: Record<string, string> = { Air: '已播出', Today: '今日', NA: '未播出' };

export default function SubjectDetail() {
  const { id } = useParams();
  const { data: sub, isLoading, isError } = useQuery({ queryKey: ['subject', id], queryFn: () => subjectsApi.detail(id!), enabled: !!id });
  const { data: eps } = useQuery({ queryKey: ['subject', id, 'episodes'], queryFn: () => subjectsApi.episodes(id!), enabled: !!id });

  if (isLoading) {
    return (
      <div className="mx-auto w-full max-w-[1280px] p-6">
        <div className="flex gap-8">
          <Skeleton className="h-[267px] w-[200px] shrink-0 rounded-lg" />
          <div className="flex-1 space-y-3">
            <Skeleton className="h-8 w-2/3" />
            <Skeleton className="h-4 w-1/3" />
            <Skeleton className="h-24 w-full" />
          </div>
        </div>
      </div>
    );
  }
  if (isError || !sub) {
    return <p className="py-16 text-center text-sm text-muted-foreground">条目加载失败，请稍后重试</p>;
  }

  const scorePct = sub.score > 0 ? (Math.min(sub.score, 10) / 10) * 100 : 0;

  return (
    <div className="mx-auto w-full max-w-[1280px] p-6">
      <div className="flex flex-col gap-8 md:flex-row">
        <aside className="w-full shrink-0 md:w-[200px]">
          <div className="md:sticky md:top-20">
            <div className="aspect-[3/4] overflow-hidden rounded-lg bg-muted">
              {sub.image
                ? <img src={sub.image} alt={sub.nameCn ?? sub.name} className="size-full object-cover" />
                : <div className="flex h-full items-center justify-center text-sm text-muted-foreground">暂无封面</div>}
            </div>
            <div className="mt-4"><CollectionActions subjectId={sub.id} eps={sub.eps} /></div>
          </div>
        </aside>

        <div className="min-w-0 flex-1 md:max-w-[920px]">
          <h1 className="text-2xl font-semibold [text-wrap:balance]">{sub.nameCn ?? sub.name}</h1>
          {sub.nameCn && <div className="text-sm text-muted-foreground">{sub.name}</div>}

          <section className="mt-4 flex items-center gap-3" aria-label={`评分 ${sub.score > 0 ? sub.score.toFixed(1) : '暂无'}`}>
            <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
              <span className="block h-full rounded-full bg-primary" style={{ width: `${scorePct}%` }} />
            </div>
            <span className="text-lg font-semibold tabular-nums">{sub.score > 0 ? sub.score.toFixed(1) : '未评分'}</span>
          </section>

          <SubjectInfoCards
            className="mt-4"
            rank={sub.rank}
            eps={sub.eps}
            airDate={sub.airDate}
            type={sub.type}
            collectionTotal={sub.collectionTotal}
          />

          {sub.summary && (
            <section className="mt-6">
              <h2 className="mb-2 text-lg font-medium">简介</h2>
              <p className="whitespace-pre-wrap leading-relaxed">{sub.summary}</p>
            </section>
          )}

          {sub.tags.length > 0 && (
            <section className="mt-4">
              <h2 className="mb-2 text-lg font-medium">标签</h2>
              <div className="flex flex-wrap gap-2">
                {sub.tags.map((t) => <Badge key={t.id} variant="secondary" className="rounded-full">{t.name}</Badge>)}
              </div>
            </section>
          )}

          {sub.relations.length > 0 && (
            <section className="mt-6">
              <h2 className="mb-2 text-lg font-medium">关联条目</h2>
              <div className="flex flex-wrap gap-4">
                {sub.relations.map((r) => (
                  <div key={r.relatedSubject.id} className="w-[100px]">
                    <Badge variant="outline" className="mb-1 rounded-full">{r.relation}</Badge>
                    <Link to={`/subject/${r.relatedSubject.id}`} className="block rounded-lg border p-2">
                      <SubjectCard subject={r.relatedSubject} />
                    </Link>
                  </div>
                ))}
              </div>
            </section>
          )}

          <section className="mt-6">
            <h2 className="mb-2 text-lg font-medium">剧集</h2>
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>#</TableHead>
                    <TableHead>标题</TableHead>
                    <TableHead>中文名</TableHead>
                    <TableHead>放送日</TableHead>
                    <TableHead>状态</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(eps ?? []).map((ep) => (
                    <TableRow key={ep.id}>
                      <TableCell>{ep.sort}</TableCell>
                      <TableCell>{ep.name}</TableCell>
                      <TableCell>{ep.nameCn}</TableCell>
                      <TableCell>{ep.airdate}</TableCell>
                      <TableCell>{EP_STATUS_LABEL[ep.status] ?? ep.status}</TableCell>
                    </TableRow>
                  ))}
                  {!eps?.length && (
                    <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">暂无剧集</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
