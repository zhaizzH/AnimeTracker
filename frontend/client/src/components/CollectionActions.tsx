import { useState, useEffect } from 'react';
import { Button, Rate, InputNumber, Space, message, Card, Typography, Empty } from 'antd';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { collectionsApi } from '@/api/collections';
import { useAuthStore } from '@/store/authStore';
import { useNavigate } from 'react-router-dom';
import type { CollectionUpdateDTO } from '@/types';
import { CollectionType } from '@/types';

const { Text } = Typography;

const typeLabels: Record<number, { label: string; color: string }> = {
  [CollectionType.WISH]: { label: '想看', color: '#1677ff' },
  [CollectionType.DOING]: { label: '在看', color: '#52c41a' },
  [CollectionType.DONE]: { label: '看过', color: '#722ed1' },
  [CollectionType.ON_HOLD]: { label: '搁置', color: '#faad14' },
  [CollectionType.DROPPED]: { label: '抛弃', color: '#ff4d4f' },
};

interface Props {
  subjectId: number;
}

export default function CollectionActions({ subjectId }: Props) {
  const { isLoggedIn } = useAuthStore();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // 查询当前收藏状态
  const { data: collection, isLoading } = useQuery({
    queryKey: ['collection', subjectId],
    queryFn: () => collectionsApi.get(subjectId),
    enabled: isLoggedIn,
  });

  const [selectedType, setSelectedType] = useState<number>(collection?.type || 0);
  const [rate, setRate] = useState(collection?.rate || 0);
  const [epStatus, setEpStatus] = useState(collection?.epStatus || 0);

  // 同步收藏数据到本地状态
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
      queryClient.invalidateQueries({ queryKey: ['collection', subjectId] });
      setSelectedType(0); setRate(0); setEpStatus(0);
      message.success('已取消收藏');
    },
    onError: (err: any) => message.error(err.message || '操作失败'),
  });

  if (!isLoggedIn) {
    return (
      <Card style={{ textAlign: 'center' }}>
        <Empty description="登录后可追番" />
        <Button type="primary" onClick={() => navigate('/login')}>去登录</Button>
      </Card>
    );
  }

  const isCollected = !!collection;

  return (
    <Card title="追番操作" loading={isLoading}>
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* 收藏类型按钮 */}
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

        {/* 评分 */}
        <Space>
          <Text>评分:</Text>
          <Rate count={10} value={rate} onChange={val => {
            setRate(val);
            if (isCollected) saveMutation.mutate({ type: selectedType as CollectionUpdateDTO['type'], rate: val, epStatus });
          }} />
        </Space>

        {/* 进度 */}
        <Space>
          <Text>进度:</Text>
          <InputNumber
            min={0} value={epStatus}
            onChange={val => {
              const v = val || 0;
              setEpStatus(v);
              if (isCollected) saveMutation.mutate({ type: selectedType as CollectionUpdateDTO['type'], rate, epStatus: v });
            }}
          />
          <Text>集</Text>
        </Space>

        {/* 取消收藏 */}
        {isCollected && (
          <Button danger onClick={() => removeMutation.mutate()}>取消收藏</Button>
        )}
      </Space>
    </Card>
  );
}
