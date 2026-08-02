import { useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import type { SubjectListVO } from '@/types';

interface SubjectCardProps {
  subject: SubjectListVO;
  extra?: ReactNode;
}

export default function SubjectCard({ subject, extra }: SubjectCardProps) {
  const navigate = useNavigate();
  const score = Number(subject.score ?? 0);

  return (
    <article className="subject-card" onClick={() => navigate(`/subject/${subject.id}`)}>
      <div className="subject-card-cover">
        <img
          alt={subject.nameCn || subject.name}
          src={subject.image || '/placeholder.png'}
        />
        <span className="subject-card-mark">
          {subject.rank ? `RANK ${subject.rank}` : 'NEW'}
        </span>
      </div>
      <div className="subject-card-body">
        <h3>{subject.nameCn || subject.name}</h3>
        <p className="subject-original">{subject.name}</p>
        <div className="subject-card-meta">
          <span className="subject-score">{score.toFixed(1)}</span>
          <span>收藏 {subject.collectionTotal ?? 0}</span>
        </div>
        {extra && <div className="subject-card-extra">{extra}</div>}
      </div>
    </article>
  );
}
