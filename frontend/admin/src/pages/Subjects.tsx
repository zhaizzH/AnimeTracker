import { useEffect, useState } from 'react';
import {
  App,
  Button,
  DatePicker,
  Drawer,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tooltip,
} from 'antd';
import type { TablePaginationConfig, TableProps } from 'antd';
import { DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { subjectsApi } from '../api/subjects';
import type { SubjectListVO, SubjectQueryParams, SubjectUpsertDTO } from '../types/api';

interface SubjectFormValues {
  name: string;
  nameCn?: string;
  bangumiId?: number;
  type?: number;
  eps?: number;
  airDate?: dayjs.Dayjs;
  image?: string;
  summary?: string;
}

const typeLabel: Record<number, string> = {
  1: '书籍',
  2: '动画',
  6: '三次元',
};

const typeColor: Record<number, string> = {
  1: '#8a6fd8',
  2: '#00b3a4',
  6: '#2f7fe8',
};

function hueOf(id: number): number {
  return Math.abs(Math.sin(id * 12.9898) * 43758.5453) % 360;
}

export default function Subjects() {
  const { message } = App.useApp();
  const [list, setList] = useState<SubjectListVO[]>([]);
  const [keyword, setKeyword] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [scoreMin, setScoreMin] = useState<number | null>(null);
  const [scoreMax, setScoreMax] = useState<number | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [weekday, setWeekday] = useState<number | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<SubjectListVO | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [createForm] = Form.useForm<SubjectFormValues>();
  const [editForm] = Form.useForm<SubjectFormValues>();

  const load = async (nextPage = page, nextSize = pageSize, nextKeyword = keyword) => {
    setLoading(true);
    try {
      const params: SubjectQueryParams = {
        q: nextKeyword.trim() || undefined,
        page: nextPage,
        size: nextSize,
        sort: 'id',
        order: 'desc',
        tag: tags.length ? tags : undefined,
        scoreMin: scoreMin ?? undefined,
        scoreMax: scoreMax ?? undefined,
        year: year ?? undefined,
        weekday: weekday ?? undefined,
      };
      const result = await subjectsApi.search(params);
      setList(result.content ?? []);
      setTotal(result.total ?? 0);
      setPage(result.page ?? nextPage);
      setPageSize(result.size ?? nextSize);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '条目加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(1, pageSize, keyword);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const refresh = () => load(page, pageSize, keyword);

  const handleSearch = () => {
    setPage(1);
    load(1, pageSize, keyword);
  };

  const handleTableChange = (pagination: TablePaginationConfig) => {
    const nextPage = pagination.current ?? 1;
    const nextSize = pagination.pageSize ?? pageSize;
    setPage(nextPage);
    setPageSize(nextSize);
    load(nextPage, nextSize, keyword);
  };

  const resetFilters = () => {
    setTags([]);
    setScoreMin(null);
    setScoreMax(null);
    setYear(null);
    setWeekday(null);
    setKeyword('');
    setPage(1);
    load(1, pageSize, '');
  };

  const animatedCount = list.filter((item) => item.type === 2).length;

  const openEdit = (row: SubjectListVO) => {
    setEditTarget(row);
    editForm.setFieldsValue({
      name: row.name,
      nameCn: row.nameCn || row.name,
      bangumiId: undefined,
      type: row.type,
      eps: row.eps,
      airDate: row.airDate ? dayjs(row.airDate) : undefined,
      image: row.image ?? '',
      summary: '',
    });
  };

  const handleCreate = async (values: SubjectFormValues) => {
    setSubmitting(true);
    try {
      const payload: SubjectUpsertDTO = {
        bangumiId: values.bangumiId,
        name: values.name,
        nameCn: values.nameCn,
        summary: values.summary,
        type: values.type,
        eps: values.eps,
        airDate: values.airDate ? values.airDate.format('YYYY-MM-DD') : undefined,
        image: values.image || undefined,
      };
      await subjectsApi.create(payload);
      message.success('条目已创建');
      setCreateOpen(false);
      createForm.resetFields();
      refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '创建失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = async (values: SubjectFormValues) => {
    if (!editTarget) return;
    setSubmitting(true);
    try {
      const payload: SubjectUpsertDTO = {
        bangumiId: values.bangumiId,
        name: values.name,
        nameCn: values.nameCn,
        summary: values.summary,
        type: values.type,
        eps: values.eps,
        airDate: values.airDate ? values.airDate.format('YYYY-MM-DD') : undefined,
        image: values.image || undefined,
      };
      await subjectsApi.update(editTarget.id, payload);
      message.success(`条目 #${editTarget.id} 已更新`);
      setEditTarget(null);
      editForm.resetFields();
      refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '更新失败');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async (row: SubjectListVO) => {
    try {
      await subjectsApi.remove(row.id);
      message.success(`条目「${row.nameCn || row.name}」已删除`);
      refresh();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除失败');
    }
  };

  const columns: TableProps<SubjectListVO>['columns'] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 72,
      className: 'num',
      render: (value: number) => `#${value}`,
    },
    {
      title: '条目',
      dataIndex: 'nameCn',
      render: (_, row) => (
        <div className="rank-cell">
          {row.image ? (
            <img className="poster-thumb" src={row.image} alt={row.nameCn || row.name} />
          ) : (
            <span
              className="poster-thumb"
              style={{
                background: `linear-gradient(135deg, hsl(${hueOf(row.id)} 42% 26%), hsl(${(hueOf(row.id) + 45) % 360} 52% 10%))`,
              }}
            >
              {(row.nameCn || row.name).slice(0, 1)}
            </span>
          )}
          <span className="subject-name">
            <b>{row.nameCn || row.name}</b>
            <span>{row.name}</span>
          </span>
        </div>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      width: 76,
      render: (value: number) => (
        <span className="type-chip" style={{ color: typeColor[value] ?? 'inherit' }}>
          {typeLabel[value] ?? `类型 ${value}`}
        </span>
      ),
    },
    {
      title: '放送',
      width: 148,
      render: (_, row) => (
        <span className="cell-muted">
          {row.airDate ?? '-'}
          {row.airWeekday > 0 ? ` · 周${row.airWeekday}` : ''}
        </span>
      ),
    },
    {
      title: '集数',
      dataIndex: 'eps',
      width: 64,
      className: 'num',
      render: (value: number) => value ?? '-',
    },
    {
      title: '评分',
      dataIndex: 'score',
      width: 76,
      className: 'num',
      render: (value: number) => (value > 0 ? Number(value).toFixed(1) : '-'),
    },
    {
      title: '收藏',
      dataIndex: 'collectionTotal',
      width: 92,
      className: 'num',
      render: (value: number) => Number(value ?? 0).toLocaleString(),
    },
    {
      title: '排名',
      dataIndex: 'rank',
      width: 76,
      className: 'num',
      render: (value: number) => (value > 0 ? `#${value}` : '-'),
    },
    {
      title: '操作',
      width: 96,
      render: (_, row) => (
        <Space size={4}>
          <Tooltip title="编辑条目">
            <Button type="text" size="small" icon={<EditOutlined />} onClick={() => openEdit(row)} />
          </Tooltip>
          <Popconfirm
            title="确认删除该条目？"
            description="删除后不可恢复。"
            okText="删除"
            cancelText="取消"
            onConfirm={() => handleRemove(row)}
          >
            <Tooltip title="删除条目">
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="dash-stack">
      <div className="dash-toolbar">
        <div>
          <div className="dash-toolbar-sub">接口 · GET /api/user/subjects/search?q=&tag=&year=&weekday=&scoreMin=&scoreMax=</div>
        </div>
        <div className="dash-toolbar-actions">
          <Tooltip title="刷新条目数据">
            <Button icon={<ReloadOutlined spin={loading} />} onClick={refresh} />
          </Tooltip>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            新增条目
          </Button>
        </div>
      </div>

      <div className="mini-stats">
        <div className="mini-stat tone-cyan">
          <div>
            <div className="mini-stat-label">条目总数</div>
            <div className="mini-stat-value">{total.toLocaleString()}</div>
          </div>
        </div>
        <div className="mini-stat tone-green">
          <div>
            <div className="mini-stat-label">当前页动画</div>
            <div className="mini-stat-value">{animatedCount}</div>
          </div>
        </div>
        <div className="mini-stat tone-amber">
          <div>
            <div className="mini-stat-label">当前页</div>
            <div className="mini-stat-value">{page}</div>
          </div>
        </div>
        <div className="mini-stat tone-blue">
          <div>
            <div className="mini-stat-label">每页条数</div>
            <div className="mini-stat-value">{pageSize}</div>
          </div>
        </div>
      </div>

      <div className="filter-panel">
        <div className="filter-item">
          <span>关键词</span>
          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="名称 / ID"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onPressEnter={handleSearch}
            style={{ width: 200 }}
          />
        </div>
        <div className="filter-item">
          <span>标签</span>
          <Select
            mode="tags"
            placeholder="输入标签回车"
            value={tags}
            onChange={setTags}
            tokenSeparators={[',']}
            style={{ width: 170 }}
          />
        </div>
        <div className="filter-item">
          <span>年份</span>
          <InputNumber min={1970} max={2100} placeholder="年份" value={year} onChange={setYear} style={{ width: 110 }} />
        </div>
        <div className="filter-item">
          <span>星期</span>
          <Select
            allowClear
            placeholder="周几"
            value={weekday}
            onChange={setWeekday}
            style={{ width: 110 }}
            options={[
              { value: 1, label: '周一' },
              { value: 2, label: '周二' },
              { value: 3, label: '周三' },
              { value: 4, label: '周四' },
              { value: 5, label: '周五' },
              { value: 6, label: '周六' },
              { value: 0, label: '周日' },
            ]}
          />
        </div>
        <div className="filter-item">
          <span>评分</span>
          <Space size={4}>
            <InputNumber min={0} max={10} step={0.1} placeholder="最低" value={scoreMin} onChange={setScoreMin} style={{ width: 88 }} />
            <span>~</span>
            <InputNumber min={0} max={10} step={0.1} placeholder="最高" value={scoreMax} onChange={setScoreMax} style={{ width: 88 }} />
          </Space>
        </div>
        <Button type="primary" ghost icon={<SearchOutlined />} onClick={handleSearch}>
          搜索
        </Button>
        <Button onClick={resetFilters}>重置</Button>
        <div className="filter-spacer" />
        <span className="filter-count">总数 {total.toLocaleString()}</span>
      </div>

      <section className="panel table-panel">
        <div className="panel-head">
          <div>
            <h3 className="panel-title">
              <span className="seq">01</span>番剧条目
            </h3>
            <div className="panel-sub">创建 / 更新 / 删除均走管理接口</div>
          </div>
          <span className="panel-note">第 {page}/{Math.max(1, Math.ceil(total / pageSize))} 页</span>
        </div>
        <Table<SubjectListVO>
          rowKey="id"
          columns={columns}
          dataSource={list}
          loading={loading}
          size="middle"
          onChange={handleTableChange}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            pageSizeOptions: [10, 20, 50, 100],
            showTotal: (count) => `共 ${count} 条`,
          }}
          scroll={{ x: 1120 }}
        />
      </section>

      <Modal
        title="新增番剧条目"
        open={createOpen}
        onCancel={() => {
          setCreateOpen(false);
          createForm.resetFields();
        }}
        onOk={() => createForm.submit()}
        okText="创建条目"
        cancelText="取消"
        width={680}
        confirmLoading={submitting}
        destroyOnHidden
      >
        <Form form={createForm} layout="vertical" className="form-grid" onFinish={handleCreate}>
          <Form.Item name="name" label="原名 / 日文名" rules={[{ required: true, message: '请输入条目原名' }]}>
            <Input placeholder="BanG Dream! Ave Mujica" />
          </Form.Item>
          <Form.Item name="nameCn" label="中文名">
            <Input placeholder="中文标题（可选）" />
          </Form.Item>
          <Form.Item name="bangumiId" label="Bangumi ID">
            <InputNumber min={1} style={{ width: '100%' }} placeholder="482901" />
          </Form.Item>
          <Form.Item name="type" label="条目类型" initialValue={2}>
            <Select
              options={[
                { value: 2, label: '动画 (2)' },
                { value: 1, label: '书籍 (1)' },
                { value: 6, label: '三次元 (6)' },
              ]}
            />
          </Form.Item>
          <Form.Item name="eps" label="总集数">
            <InputNumber min={0} style={{ width: '100%' }} placeholder="13" />
          </Form.Item>
          <Form.Item name="airDate" label="放送日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="image" label="封面图 URL" className="span-2">
            <Input placeholder="https://..." />
          </Form.Item>
          <Form.Item name="summary" label="简介" className="span-2">
            <Input.TextArea rows={3} placeholder="条目简介（可选）" />
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title={editTarget ? `编辑条目 #${editTarget.id}` : '编辑条目'}
        width={520}
        open={!!editTarget}
        onClose={() => {
          setEditTarget(null);
          editForm.resetFields();
        }}
        extra={
          <Space>
            <Button
              onClick={() => {
                setEditTarget(null);
                editForm.resetFields();
              }}
            >
              取消
            </Button>
            <Button type="primary" loading={submitting} onClick={() => editForm.submit()}>
              保存修改
            </Button>
          </Space>
        }
      >
        <Form form={editForm} layout="vertical" className="form-grid" onFinish={handleEdit}>
          <Form.Item name="name" label="原名 / 日文名" rules={[{ required: true, message: '请输入条目原名' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="nameCn" label="中文名">
            <Input />
          </Form.Item>
          <Form.Item name="bangumiId" label="Bangumi ID">
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="type" label="条目类型">
            <Select
              options={[
                { value: 2, label: '动画 (2)' },
                { value: 1, label: '书籍 (1)' },
                { value: 6, label: '三次元 (6)' },
              ]}
            />
          </Form.Item>
          <Form.Item name="eps" label="总集数">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="airDate" label="放送日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="image" label="封面图 URL" className="span-2">
            <Input placeholder="https://..." />
          </Form.Item>
          <Form.Item name="summary" label="简介" className="span-2">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
