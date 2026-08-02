import { useState } from 'react';
import { Tabs, Table, Rate, InputNumber, Button, Space, Popconfirm } from 'antd';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { collectionsApi } from '@/api/collections';
import { useCollections } from '@/hooks/useCollections';
import PageHeading from '@/components/PageHeading';
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
      page,
      size: 20,
    }),
  });

  const columns = [
    {
      title: '封面',
      dataIndex: ['subject', 'image'],
      key: 'image',
      width: 76,
      render: (src: string, record: UserCollectionVO) => (
        <img
          src={src || '/placeholder.png'}
          alt={record.subject.name}
          className="collection-cover"
          onClick={() => navigate(`/subject/${record.subjectId}`)}
        />
      ),
    },
    {
      title: '标题',
      key: 'title',
      width: 220,
      render: (_: any, record: UserCollectionVO) => (
        <a className="collection-title" onClick={() => navigate(`/subject/${record.subjectId}`)}>
          {record.subject.nameCn || record.subject.name}
        </a>
      ),
    },
    {
      title: '评分',
      dataIndex: 'rate',
      key: 'rate',
      width: 210,
      render: (rate: number, record: UserCollectionVO) => (
        <Rate
          count={10}
          value={rate}
          onChange={val => saveMutation.mutate({
            subjectId: record.subjectId,
            data: { type: record.type, rate: val, epStatus: record.epStatus },
          })}
        />
      ),
    },
    {
      title: '进度',
      key: 'progress',
      width: 160,
      render: (_: any, record: UserCollectionVO) => (
        <Space>
          <InputNumber
            min={0}
            value={record.epStatus}
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
      title: '操作',
      key: 'actions',
      width: 110,
      render: (_: any, record: UserCollectionVO) => (
        <Popconfirm title="确定取消收藏？" onConfirm={() => removeMutation.mutate(record.subjectId)}>
          <Button size="small" danger>取消收藏</Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <PageHeading
        index="04 / LIBRARY"
        title="我的收藏"
        subtitle="想看、在看、看过，都记在这一页"
      />

      <Tabs
        className="paper-tabs"
        activeKey={type}
        onChange={val => { setType(val); setPage(1); }}
        items={typeTabs.map(t => ({ key: t.key, label: t.label }))}
      />

      <div className="index-result-line">
        <span>共 <strong>{(data as any)?.total || 0}</strong> 条记录</span>
        <span style={{ color: 'var(--ink-faint)', fontFamily: 'var(--mono)', fontSize: 11 }}>
          EPISODE LOG
        </span>
      </div>

      <Table
        className="paper-table"
        dataSource={(data as any)?.content || []}
        columns={columns}
        rowKey="id"
        scroll={{ x: 820 }}
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
