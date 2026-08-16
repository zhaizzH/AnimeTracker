import type { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { copy } from '@/content/zh-CN';
import { getPublicApi } from '@/lib/api/public-client';
import { ApiError } from '@/lib/api/errors';
import { SubjectDetail } from '@/features/subjects/subject-detail';
import type { SubjectDetailModel, EpisodeModel } from '@/features/subjects/subject-detail';
import { parseSubjectId, detailExcerpt } from '@/features/subjects/detail-meta';

type PageProps = { params: Promise<{ id: string }> };

/** 绝对 canonical 地址，来自 NEXT_PUBLIC_SITE_URL（无配置时省略 canonical）。 */
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL;

function buildCanonical(path: string): { alternates?: { canonical: string } } {
  return SITE_URL ? { alternates: { canonical: `${SITE_URL.replace(/\/$/, '')}${path}` } } : {};
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { id: raw } = await params;
  const id = parseSubjectId(raw);
  if (Number.isNaN(id)) notFound();

  const api = getPublicApi();
  const subject = await api.getSubject(id).catch((err: unknown) => {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  });
  if (!subject) notFound();

  const title = subject.nameCn || subject.name || copy.brand;
  const description = subject.summary ? detailExcerpt(subject.summary) : copy.home.tagline;

  return {
    title: `${title} · ${copy.brand}`,
    description,
    ...(subject.image ? { openGraph: { images: [{ url: subject.image }] } } : {}),
    ...buildCanonical(`/subjects/${id}`),
  };
}

export default async function SubjectPage({ params }: PageProps) {
  const { id: raw } = await params;
  const id = parseSubjectId(raw);
  if (Number.isNaN(id)) notFound();

  const api = getPublicApi();
  const [subject, episodes] = await Promise.all([
    api.getSubject(id),
    api.getEpisodes(id),
  ]).catch((err: unknown) => {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  });

  if (!subject) notFound();

  return (
    <SubjectDetail
      subject={subject as SubjectDetailModel}
      episodes={(episodes ?? []) as EpisodeModel[]}
    />
  );
}
