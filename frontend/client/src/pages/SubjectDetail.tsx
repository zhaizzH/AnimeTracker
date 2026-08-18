import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { Descriptions, Empty, Space, Spin, Table, Tag } from 'antd';
import { subjectsApi } from '@shared';
import { CollectionActions } from '../components/CollectionActions';

export default function SubjectDetail() {
  const { id } = useParams();
  const { data: sub, isLoading, isError } = useQuery({ queryKey: ['subject', id], queryFn: () => subjectsApi.detail(id!), enabled: !!id });
  const { data: eps } = useQuery({ queryKey: ['subject', id, 'episodes'], queryFn: () => subjectsApi.episodes(id!), enabled: !!id });
  if (isLoading) return <Spin style={{ display: 'block', margin: 40 }} />;
  if (isError || !sub) return <Empty description="条目加载失败，请稍后重试" style={{ margin: 60 }} />;
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <div style={{ display: 'flex', gap: 24 }}>
        <img src={sub.image ?? undefined} alt={sub.nameCn ?? sub.name} style={{ width: 180, aspectRatio: '3/4', objectFit: 'cover', background: '#eee', borderRadius: 8 }} />
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 28 }}>{sub.nameCn ?? sub.name}</h1>
          {sub.nameCn && <div style={{ color: '#888' }}>{sub.name}</div>}
          <Descriptions column={3} size="small" style={{ margin: '12px 0' }} items={[
            { key: 'score', label: '评分', children: sub.score || '—' },
            { key: 'rank', label: '排名', children: sub.rank || '—' },
            { key: 'eps', label: '集数', children: sub.eps },
            { key: 'air', label: '放送', children: sub.airDate || '—' },
            { key: 'type', label: '类型', children: sub.type === 2 ? '动画' : sub.type },
            { key: 'hot', label: '收藏', children: sub.collectionTotal },
          ]} />
          <CollectionActions subjectId={sub.id} eps={sub.eps} />
        </div>
      </div>
      {sub.summary && <section style={{ marginTop: 24 }}><h2 style={{ fontSize: 20 }}>简介</h2><p style={{ whiteSpace: 'pre-wrap' }}>{sub.summary}</p></section>}
      {sub.tags.length > 0 && <section style={{ marginTop: 16 }}><h2 style={{ fontSize: 20 }}>标签</h2><Space wrap>{sub.tags.map((t) => <Tag key={t.id}>{t.name}</Tag>)}</Space></section>}
      {sub.relations.length > 0 && <section style={{ marginTop: 24 }}><h2 style={{ fontSize: 20 }}>关联条目</h2>{sub.relations.map((r) => <Tag key={r.relatedSubject.id} style={{ margin: 4 }}>{r.relation}: {r.relatedSubject.nameCn ?? r.relatedSubject.name}</Tag>)}</section>}
      <section style={{ marginTop: 24 }}><h2 style={{ fontSize: 20 }}>剧集</h2><Table rowKey="id" size="small" dataSource={eps} pagination={false} columns={[
        { title: '#', dataIndex: 'sort' }, { title: '标题', dataIndex: 'name' }, { title: '中文名', dataIndex: 'nameCn' },
        { title: '放送日', dataIndex: 'airdate' }, { title: '状态', dataIndex: 'status', render: (v: string) => ({ Air: '已播出', Today: '今日', NA: '未播出' }[v] ?? v) },
      ]} /></section>
    </div>
  );
}
