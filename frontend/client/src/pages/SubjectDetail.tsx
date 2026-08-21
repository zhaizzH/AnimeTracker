import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { Descriptions, Empty, Space, Spin, Table, Tag, theme } from 'antd';
import { SubjectCard, subjectsApi } from '@shared';
import { CollectionActions } from '../components/CollectionActions';

export default function SubjectDetail() {
  const { token } = theme.useToken();
  const navigate = useNavigate();
  const { id } = useParams();
  const { data: sub, isLoading, isError } = useQuery({ queryKey: ['subject', id], queryFn: () => subjectsApi.detail(id!), enabled: !!id });
  const { data: eps } = useQuery({ queryKey: ['subject', id, 'episodes'], queryFn: () => subjectsApi.episodes(id!), enabled: !!id });
  if (isLoading) return <Spin style={{ display: 'block', margin: 40 }} />;
  if (isError || !sub) return <Empty description="条目加载失败，请稍后重试" style={{ margin: 60 }} />;
  const scorePct = sub.score > 0 ? Math.min(sub.score, 10) / 10 * 100 : 0;
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <div style={{ display: 'flex', gap: 32, alignItems: 'flex-start' }}>
        <aside className="od-detail-aside">
          <img src={sub.image ?? undefined} alt={sub.nameCn ?? sub.name} style={{ width: 200, aspectRatio: '3/4', objectFit: 'cover', background: token.colorBorderSecondary, borderRadius: 8 }} />
          <div style={{ marginTop: 16 }}><CollectionActions subjectId={sub.id} eps={sub.eps} /></div>
        </aside>
        <div className="od-detail-main">
          <h1 style={{ fontSize: 28, textWrap: 'balance' }}>{sub.nameCn ?? sub.name}</h1>
          {sub.nameCn && <div style={{ color: token.colorTextTertiary }}>{sub.name}</div>}
          <section className="od-rate" aria-label={`评分 ${sub.score > 0 ? sub.score.toFixed(1) : '暂无'}`}>
            <div className="od-rate__bar"><span style={{ width: `${scorePct}%` }} /></div>
            <span className="od-rate__num">{sub.score > 0 ? sub.score.toFixed(1) : '未评分'}</span>
          </section>
          <Descriptions column={2} size="small" style={{ margin: '12px 0' }} items={[
            { key: 'rank', label: '排名', children: sub.rank || '—' },
            { key: 'eps', label: '集数', children: sub.eps },
            { key: 'air', label: '放送', children: sub.airDate || '—' },
            { key: 'type', label: '类型', children: sub.type === 2 ? '动画' : sub.type },
            { key: 'hot', label: '收藏', children: sub.collectionTotal },
          ]} />
          {sub.summary && <section style={{ marginTop: 24 }}><h2 style={{ fontSize: 20 }}>简介</h2><p style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{sub.summary}</p></section>}
          {sub.tags.length > 0 && <section style={{ marginTop: 16 }}><h2 style={{ fontSize: 20 }}>标签</h2><Space wrap>{sub.tags.map((t) => <Tag key={t.id} className="od-pill">{t.name}</Tag>)}</Space></section>}
          {sub.relations.length > 0 && <section style={{ marginTop: 24 }}><h2 style={{ fontSize: 20 }}>关联条目</h2><Space align="start" wrap>{sub.relations.map((r) => (
            <div key={r.relatedSubject.id} style={{ width: 100 }}>
              <Tag style={{ marginBottom: 4 }} className="od-pill">{r.relation}</Tag>
              <SubjectCard subject={r.relatedSubject} onClick={() => navigate(`/subject/${r.relatedSubject.id}`)} />
            </div>
          ))}</Space></section>}
          <section style={{ marginTop: 24 }}><h2 style={{ fontSize: 20 }}>剧集</h2><Table rowKey="id" size="small" dataSource={eps} pagination={false} columns={[
            { title: '#', dataIndex: 'sort' }, { title: '标题', dataIndex: 'name' }, { title: '中文名', dataIndex: 'nameCn' },
            { title: '放送日', dataIndex: 'airdate' }, { title: '状态', dataIndex: 'status', render: (v: string) => ({ Air: '已播出', Today: '今日', NA: '未播出' }[v] ?? v) },
          ]} /></section>
        </div>
      </div>
    </div>
  );
}
