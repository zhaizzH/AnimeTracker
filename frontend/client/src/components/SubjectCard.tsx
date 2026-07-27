import { Card, Typography, Rate } from 'antd';
import { useNavigate } from 'react-router-dom';
import type { SubjectListVO } from '@/types';

const { Text } = Typography;

interface SubjectCardProps {
  subject: SubjectListVO;
  extra?: React.ReactNode; // 额外信息，如放送时间
}

export default function SubjectCard({ subject, extra }: SubjectCardProps) {
  const navigate = useNavigate();

  return (
    <Card
      hoverable
      style={{ width: 200 }}
      cover={
        <img
          alt={subject.nameCn || subject.name}
          src={subject.image || '/placeholder.png'}
          style={{ height: 280, objectFit: 'cover' }}
          onClick={() => navigate(`/subject/${subject.id}`)}
        />
      }
      styles={{ body: { padding: 12 } }}
    >
      <Text ellipsis style={{ display: 'block', fontWeight: 'bold' }}>
        {subject.nameCn || subject.name}
      </Text>
      <Text type="secondary" ellipsis style={{ display: 'block', fontSize: 12 }}>
        {subject.name}
      </Text>
      <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Rate disabled value={Math.round(subject.score / 2)} count={5} style={{ fontSize: 14 }} />
        <Text type="secondary" style={{ fontSize: 12 }}>{subject.score}</Text>
      </div>
      {extra && <div style={{ marginTop: 4 }}>{extra}</div>}
    </Card>
  );
}
