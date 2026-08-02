import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Table, Spin, Empty } from 'antd';
import { subjectsApi } from '@/api/subjects';
import CollectionActions from '@/components/CollectionActions';
import PageHeading from '@/components/PageHeading';

const typeMap: Record<number, string> = {
  2: '动画',
  1: '书籍',
  3: '音乐',
  4: '游戏',
  6: '三次元',
};

const episodeColumns = [
  { title: '#', dataIndex: 'sort', key: 'sort', width: 60 },
  { title: '标题', dataIndex: 'name', key: 'name' },
  { title: '中文名', dataIndex: 'nameCn', key: 'nameCn' },
  { title: '放送日', dataIndex: 'airdate', key: 'airdate', width: 110 },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 90,
    render: (s: 'Air' | 'Today' | 'NA') => {
      const label = { Air: '已播出', Today: '今日播出', NA: '未播出' }[s] ?? s;
      return <span className={`ep-status ${s || 'NA'}`}>{label}</span>;
    },
  },
];

export default function SubjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const subjectId = Number(id);

  const { data: subject, isLoading } = useQuery({
    queryKey: ['subject', subjectId],
    queryFn: () => subjectsApi.detail(subjectId),
    enabled: !!subjectId,
  });

  const { data: episodes } = useQuery({
    queryKey: ['episodes', subjectId],
    queryFn: () => subjectsApi.episodes(subjectId),
    enabled: !!subjectId,
  });

  if (isLoading) return <Spin className="paper-loading" />;
  if (!subject) return <Empty description="条目不存在" style={{ marginTop: 80 }} />;

  const metaItems = [
    { label: '评分', value: subject.score ?? '-' },
    { label: '排名', value: subject.rank ? `#${subject.rank}` : '-' },
    { label: '类型', value: typeMap[subject.type] || subject.type },
    { label: '放送日', value: subject.airDate || '-' },
    { label: '总集数', value: subject.eps ? `${subject.eps} 集` : '-' },
    { label: '收藏数', value: `${subject.collectionTotal ?? 0}` },
  ];

  return (
    <div>
      <PageHeading
        index={`FILE / ${subjectId}`}
        title="条目档案"
        subtitle={`${subject.nameCn || subject.name} · ${subject.name}`}
      />

      <div className="dossier-main">
        <div className="dossier-cover">
          <img src={subject.image || '/placeholder.png'} alt={subject.name} />
        </div>

        <div>
          <h2 className="dossier-title">{subject.nameCn || subject.name}</h2>
          <p className="dossier-original">{subject.name}</p>

          <dl className="dossier-meta">
            {metaItems.map(item => (
              <div key={item.label}>
                <dt>{item.label}</dt>
                <dd>{item.value}</dd>
              </div>
            ))}
          </dl>

          <CollectionActions subjectId={subjectId} />
        </div>
      </div>

      {subject.summary && (
        <section className="dossier-section">
          <h2>简介 / SUMMARY</h2>
          <p className="dossier-summary">{subject.summary}</p>
        </section>
      )}

      {subject.tags?.length > 0 && (
        <section className="dossier-section">
          <h2>标签 / TAGS</h2>
          <div className="tag-list">
            {subject.tags.map(tag => (
              <span
                key={tag.id}
                className="tag-item"
                onClick={() => navigate(`/anime?tag=${tag.name}`)}
              >
                {tag.name} ({tag.count})
              </span>
            ))}
          </div>
        </section>
      )}

      {subject.relations?.length > 0 && (
        <section className="dossier-section">
          <h2>关联条目 / RELATED</h2>
          <div className="relation-grid">
            {subject.relations.map((rel, idx) => (
              <div
                key={idx}
                className="relation-item"
                onClick={() => navigate(`/subject/${rel.relatedSubject.id}`)}
              >
                <img
                  src={rel.relatedSubject.image || '/placeholder.png'}
                  alt={rel.relatedSubject.name}
                />
                <div className="relation-item-body">
                  <span className="relation-type">{rel.relation}</span>
                  <p>{rel.relatedSubject.nameCn || rel.relatedSubject.name}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {episodes && episodes.length > 0 && (
        <section className="dossier-section">
          <h2>剧集列表 / EPISODES</h2>
          <Table
            className="paper-table"
            dataSource={episodes}
            columns={episodeColumns}
            rowKey="id"
            pagination={false}
            size="small"
          />
        </section>
      )}
    </div>
  );
}
