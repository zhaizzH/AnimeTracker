import { useState, useEffect } from 'react';
import { Button, Rate, InputNumber, Space, message, Typography } from 'antd';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { collectionsApi } from '@/api/collections';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import type { CollectionUpdateDTO } from '@/types';
import { CollectionType } from '@/types';

const { Text } = Typography;

const typeLabels: Record<number, { label: string; color: string }> = {
  [CollectionType.WISH]: { label: '想看', color: '#3c5a6b' },
  [CollectionType.DOING]: { label: '在看', color: '#3f6b4f' },
  [CollectionType.DONE]: { label: '看过', color: '#a67c2d' },
  [CollectionType.ON_HOLD]: { label: '搁置', color: '#8a8172' },
  [CollectionType.DROPPED]: { label: '抛弃', color: '#c13a24' },
};

interface Props {
  subjectId: number;
}

export default function CollectionActions({ subjectId }: Props) {
  const { isLoggedIn } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: collection, isLoading } = useQuery({
    queryKey: ['collection', subjectId],
    queryFn: () => collectionsApi.get(subjectId),
    enabled: isLoggedIn,
  });

  const [selectedType, setSelectedType] = useState<number>(collection?.type || 0);
  const [rate, setRate] = useState(collection?.rate || 0);
  const [epStatus, setEpStatus] = useState(collection?.epStatus || 0);

  useEffect(() => {
    if (collection) {
      setSelectedType(collection.type);
      setRate(collection.rate);
      setEpStatus(collection.epStatus);
    }
  }, [collection]);

  const saveMutation = useMutation({
    mutationFn: (dto: CollectionUpdateDTO) => collectionsApi.save(subjectId, dto),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collection', subjectId] });
      message.success('保存成功');
    },
    onError: (err: any) => message.error(err.message || '操作失败'),
  });

  const removeMutation = useMutation({
    mutationFn: () => collectionsApi.remove(subjectId),
    onSuccess: () => {
      queryClient.setQueryData(['collection', subjectId], null);
      setSelectedType(0); setRate(0); setEpStatus(0);
      message.success('已取消收藏');
    },
    onError: (err: any) => message.error(err.message || '操作失败'),
  });

  if (!isLoggedIn) {
    return (
      <div className="collection-panel" style={{ textAlign: 'center' }}>
        <p style={{ margin: '0 0 12px', color: 'var(--ink-soft)' }}>登录后可追番</p>
        <Button type="primary" onClick={() => navigate('/login')}>去登录</Button>
      </div>
    );
  }

  const isCollected = !!collection;

  return (
    <div className="collection-panel" style={{ opacity: isLoading ? 0.6 : 1 }}>
      <div className="collection-panel-head">
        <span>追番操作</span>
        <span>COLLECTION</span>
      </div>
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Space wrap>
          {Object.entries(typeLabels).map(([type, { label, color }]) => (
            <Button
              key={type}
              type={selectedType === Number(type) ? 'primary' : 'default'}
              style={selectedType === Number(type) ? { background: color, borderColor: color } : {}}
              onClick={() => {
                setSelectedType(Number(type));
                saveMutation.mutate({ type: Number(type) as CollectionUpdateDTO['type'], rate, epStatus });
              }}
            >
              {label}
            </Button>
          ))}
        </Space>

        <Space wrap>
          <Text style={{ color: 'var(--ink-soft)' }}>评分:</Text>
          <Rate count={10} value={rate} onChange={val => {
            setRate(val);
            if (isCollected) saveMutation.mutate({ type: selectedType as CollectionUpdateDTO['type'], rate: val, epStatus });
          }} />
        </Space>

        <Space wrap>
          <Text style={{ color: 'var(--ink-soft)' }}>进度:</Text>
          <InputNumber
            min={0} value={epStatus}
            onChange={val => {
              const v = val || 0;
              setEpStatus(v);
              if (isCollected) saveMutation.mutate({ type: selectedType as CollectionUpdateDTO['type'], rate, epStatus: v });
            }}
          />
          <Text style={{ color: 'var(--ink-soft)' }}>集</Text>
        </Space>

        {isCollected && (
          <Button danger onClick={() => removeMutation.mutate()}>取消收藏</Button>
        )}
      </Space>
    </div>
  );
}
