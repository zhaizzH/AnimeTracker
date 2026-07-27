import { useState } from 'react';
import { Tabs, Table, Rate, InputNumber, Button, Space, Image, Popconfirm } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { collectionsApi } from '@/api/collections';
import { useCollections } from '@/hooks/useCollections';
import { COLLECTION_TYPE_LABELS } from '@/utils';
import type { UserCollectionVO } from '@/types';

const typeTabs = [
  { key: '', label: '全部' },
  ...Object.entries(COLLECTION_TYPE_LABELS).map(([key, label]) => ({ key, label })),
];

export default function MyCollections() {
  const [type, setType] = useState<string>('');
  const [page, setPage] = useState(1);
  const navigate = useNavigate();
  const { saveMutation, removeMutation, epStatusMutation } = useCollections();

  const { data, isLoading } = useQuery({
    queryKey: ['collections', type, page],
    queryFn: () => collectionsApi.list({
      type: type ? parseInt(type) : undefined,
      page, size: 20,
    }),
  });

  const columns = [
    {
      title: '封面', dataIndex: ['subject', 'image'], key: 'image', width: 80,
      render: (src: string, record: UserCollectionVO) => (
        <Image src={src} alt={record.subject.name}
          style={{ width: 48, height: 64, objectFit: 'cover', cursor: 'pointer' }}
          preview={false}
          onClick={() => navigate(`/subject/${record.subjectId}`)} />
      ),
    },
    {
      title: '标题', key: 'title', width: 200,
      render: (_: any, record: UserCollectionVO) => (
        <a onClick={() => navigate(`/subject/${record.subjectId}`)}>
          {record.subject.nameCn || record.subject.name}
        </a>
      ),
    },
    {
      title: '评分', dataIndex: 'rate', key: 'rate', width: 200,
      render: (rate: number, record: UserCollectionVO) => (
        <Rate count={10} value={rate}
          onChange={val => saveMutation.mutate({
            subjectId: record.subjectId,
            data: { type: record.type, rate: val, epStatus: record.epStatus },
          })} />
      ),
    },
    {
      title: '进度', key: 'progress', width: 160,
      render: (_: any, record: UserCollectionVO) => (
        <Space>
          <InputNumber
            min={0} value={record.epStatus}
            onChange={val => epStatusMutation.mutate({
              subjectId: record.subjectId,
              epStatus: val || 0,
            })}
            style={{ width: 70 }}
          />
          <span>/ {record.subject.eps || '?'}</span>
        </Space>
      ),
    },
    {
      title: '操作', key: 'actions', width: 120,
      render: (_: any, record: UserCollectionVO) => (
        <Popconfirm
          title="确定取消收藏？"
          onConfirm={() => removeMutation.mutate(record.subjectId)}
        >
          <Button size="small" danger>取消收藏</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <Tabs
        activeKey={type}
        onChange={val => { setType(val); setPage(1); }}
        items={typeTabs.map(t => ({ key: t.key, label: t.label }))}
      />
      <Table
        dataSource={(data as any)?.content || []}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: page,
          total: (data as any)?.total || 0,
          pageSize: 20,
          onChange: setPage,
          showTotal: total => `共 ${total} 条`,
        }}
      />
    </div>
  );
}
