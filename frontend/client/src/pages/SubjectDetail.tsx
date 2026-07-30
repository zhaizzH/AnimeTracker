import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Descriptions, Tag, Table, Spin, Card, Typography, Row, Col, Image } from 'antd';
import { subjectsApi } from '@/api/subjects';
import CollectionActions from '@/components/CollectionActions';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;

const typeMap: Record<number, string> = { 2: '动画', 1: '书籍', 3: '音乐', 4: '游戏', 6: '三次元' };

const episodeColumns = [
  { title: '#', dataIndex: 'sort', key: 'sort', width: 60 },
  { title: '标题', dataIndex: 'name', key: 'name' },
  { title: '中文名', dataIndex: 'nameCn', key: 'nameCn' },
  { title: '放送日', dataIndex: 'airdate', key: 'airdate', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80,
    render: (s: 'Air' | 'Today' | 'NA') => {
      const label = { Air: '已播出', Today: '今日播出', NA: '未播出' }[s] ?? s;
      const color = s === 'Air' ? 'green' : s === 'Today' ? 'blue' : 'default';
      return <Tag color={color}>{label}</Tag>;
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

  if (isLoading) return <Spin style={{ display: 'block', margin: '40px auto' }} />;
  if (!subject) return <div>番剧不存在</div>;

  return (
    <div>
      <Row gutter={[24, 24]}>
        {/* 左侧封面 */}
        <Col xs={24} sm={8} md={6}>
          <Image src={subject.image} alt={subject.name} style={{ width: '100%', borderRadius: 8 }} />
        </Col>

        {/* 右侧信息 */}
        <Col xs={24} sm={16} md={18}>
          <Title level={3}>{subject.nameCn || subject.name}</Title>
          <Paragraph type="secondary">{subject.name}</Paragraph>
          <Descriptions column={{ xs: 1, sm: 2 }} size="small">
            <Descriptions.Item label="评分">{subject.score}</Descriptions.Item>
            <Descriptions.Item label="排名">#{subject.rank}</Descriptions.Item>
            <Descriptions.Item label="类型">{typeMap[subject.type] || subject.type}</Descriptions.Item>
            <Descriptions.Item label="放送日">{subject.airDate}</Descriptions.Item>
            <Descriptions.Item label="总集数">{subject.eps}</Descriptions.Item>
            <Descriptions.Item label="收藏数">{subject.collectionTotal}</Descriptions.Item>
          </Descriptions>

          {/* 追番操作 */}
          <div style={{ marginTop: 16 }}>
            <CollectionActions subjectId={subjectId} />
          </div>
        </Col>
      </Row>

      {/* 简介 */}
      {subject.summary && (
        <Card title="简介" style={{ marginTop: 24 }}>
          <Paragraph>{subject.summary}</Paragraph>
        </Card>
      )}

      {/* 标签 */}
      {subject.tags?.length > 0 && (
        <Card title="标签" style={{ marginTop: 16 }}>
          {subject.tags.map(tag => (
            <Tag key={tag.id} style={{ cursor: 'pointer' }}
              onClick={() => navigate(`/anime?tag=${tag.name}`)}>
              {tag.name} ({tag.count})
            </Tag>
          ))}
        </Card>
      )}

      {/* 关联条目 */}
      {subject.relations?.length > 0 && (
        <Card title="关联条目" style={{ marginTop: 16 }}>
          <Row gutter={[12, 12]}>
            {subject.relations.map((rel, idx) => (
              <Col key={idx}>
                <Card
                  hoverable
                  size="small"
                  style={{ width: 160 }}
                  onClick={() => navigate(`/subject/${rel.relatedSubject.id}`)}
                >
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {rel.relation}
                  </Typography.Text>
                  <img src={rel.relatedSubject.image} alt={rel.relatedSubject.name}
                    style={{ width: '100%', height: 120, objectFit: 'cover', margin: '4px 0' }} />
                  <Typography.Text ellipsis style={{ display: 'block' }}>
                    {rel.relatedSubject.nameCn || rel.relatedSubject.name}
                  </Typography.Text>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* 剧集列表 */}
      {episodes && episodes.length > 0 && (
        <Card title="剧集列表" style={{ marginTop: 16 }}>
          <Table
            dataSource={episodes}
            columns={episodeColumns}
            rowKey="id"
            pagination={false}
            size="small"
          />
        </Card>
      )}
    </div>
  );
}
