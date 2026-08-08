import { useEffect, useState } from 'react';
import {
  App,
  Button,
  DatePicker,
  Descriptions,
  Drawer,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Upload,
} from 'antd';
import type { TablePaginationConfig, TableProps } from 'antd';
import type { UploadProps } from 'antd';
import {
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  SearchOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { subjectsApi, uploadCommonFile } from '../api/subjects';
import type {
  EpisodeVO,
  SubjectDetailVO,
  SubjectListVO,
  SubjectQueryParams,
  SubjectUpsertDTO,
} from '../types/api';

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

const episodeTypeLabel: Record<number, string> = {
  0: '本篇',
  1: 'SP',
  2: 'OP',
  3: 'ED',
  4: '预告',
};

const episodeStatusMeta: Record<string, { label: string; cls: string }> = {
  Air: { label: '已放送', cls: 'success' },
  Today: { label: '今日', cls: 'running' },
  NA: { label: '未放送', cls: 'neutral' },
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
  const [detailTarget, setDetailTarget] = useState<SubjectDetailVO | null>(null);
  const [detailEpisodes, setDetailEpisodes] = useState<EpisodeVO[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);
  const [coverUploading, setCoverUploading] = useState(false);
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

  const openEdit = async (row: SubjectListVO) => {
    setEditTarget(row);
    const base = {
      name: row.name,
      nameCn: row.nameCn || row.name,
      bangumiId: undefined,
      type: row.type,
      eps: row.eps,
      airDate: row.airDate ? dayjs(row.airDate) : undefined,
      image: row.image ?? '',
      summary: '',
    };
    try {
      const detail = await subjectsApi.detail(row.id);
      editForm.setFieldsValue({
        ...base,
        bangumiId: detail.bangumiId ?? undefined,
        summary: detail.summary ?? '',
        image: detail.image ?? row.image ?? '',
      });
    } catch (error) {
      editForm.setFieldsValue(base);
      message.warning(error instanceof Error ? `详情加载失败，已按列表数据预填：${error.message}` : '详情加载失败，已按列表数据预填');
    }
  };

  const openDetail = async (row: SubjectListVO) => {
    setDetailLoading(true);
    setDetailTarget(null);
    setDetailEpisodes([]);
    try {
      const [detail, episodes] = await Promise.all([subjectsApi.detail(row.id), subjectsApi.episodes(row.id)]);
      setDetailTarget(detail);
      setDetailEpisodes(episodes ?? []);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '条目详情加载失败');
      setDetailTarget(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const uploadCover: UploadProps['beforeUpload'] = async (file) => {
    const isImage = ['image/jpeg', 'image/png', 'image/webp'].includes(file.type);
    if (!isImage) {
      message.error('仅支持 JPG / PNG / WebP 图片');
      return Upload.LIST_IGNORE;
    }
    setCoverUploading(true);
    try {
      const url = await uploadCommonFile(file as File, 'cover');
      editTarget
        ? editForm.setFieldValue('image', url)
        : createForm.setFieldValue('image', url);
      message.success('封面已上传，保存条目后生效');
    } catch (error) {
      message.error(error instanceof Error ? error.message : '封面上传失败');
    } finally {
      setCoverUploading(false);
    }
    return Upload.LIST_IGNORE;
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
      width: 136,
      render: (_, row) => (
        <Space size={4}>
          <Tooltip title="查看详情">
            <Button type="text" size="small" icon={<EyeOutlined />} onClick={() => openDetail(row)} />
          </Tooltip>
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
          <div className="dash-toolbar-sub">接口 · GET /api/client/subjects/search?q=&tag=&year=&weekday=&scoreMin=&scoreMax=</div>
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
          <Form.Item name="bangumiId" label="Bangumi ID" rules={[{ required: true, message: '请输入 Bangumi ID' }]}>
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
          <Form.Item name="image" label="封面图" className="span-2" extra="可上传 JPG / PNG / WebP，或直接填写图片 URL">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload.Dragger
                accept="image/jpeg,image/png,image/webp"
                showUploadList={false}
                beforeUpload={uploadCover}
                disabled={coverUploading}
                style={{ padding: 10 }}
              >
                <UploadOutlined style={{ fontSize: 22, color: 'var(--cyan)' }} />
                <div>点击或拖拽上传封面</div>
              </Upload.Dragger>
              <Input placeholder="https://... 或上传后自动填充" />
            </Space>
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
          <Form.Item name="bangumiId" label="Bangumi ID" rules={[{ required: true, message: '请输入 Bangumi ID' }]}>
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
          <Form.Item name="image" label="封面图" className="span-2" extra="上传 JPG / PNG / WebP，或直接修改 URL">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Upload.Dragger
                accept="image/jpeg,image/png,image/webp"
                showUploadList={false}
                beforeUpload={uploadCover}
                disabled={coverUploading}
                style={{ padding: 10 }}
              >
                <UploadOutlined style={{ fontSize: 22, color: 'var(--cyan)' }} />
                <div>{coverUploading ? '上传中...' : '点击或拖拽更换封面'}</div>
              </Upload.Dragger>
              <Input placeholder="https://..." />
            </Space>
          </Form.Item>
          <Form.Item name="summary" label="简介" className="span-2">
            <Input.TextArea rows={4} />
          </Form.Item>
        </Form>
      </Drawer>

      <Drawer
        title={detailTarget ? `条目详情 · ${detailTarget.nameCn || detailTarget.name}` : '条目详情'}
        width={760}
        open={detailLoading || !!detailTarget}
        onClose={() => {
          setDetailTarget(null);
          setDetailEpisodes([]);
        }}
        extra={
          detailTarget && (
            <Button
              icon={<EditOutlined />}
              onClick={() => {
                const target = detailTarget;
                setDetailTarget(null);
                openEdit(target);
              }}
            >
              编辑条目
            </Button>
          )
        }
      >
        {!detailTarget ? (
          <div className="detail-empty" style={{ color: 'var(--text-faint)', padding: '48px 0', textAlign: 'center' }}>
            加载中...
          </div>
        ) : (
          <div className="dash-stack">
            <div className="rank-cell">
              {detailTarget.image ? (
                <img
                  className="poster-thumb"
                  src={detailTarget.image}
                  alt={detailTarget.nameCn || detailTarget.name}
                  style={{ width: 72, height: 100 }}
                />
              ) : (
                <span
                  className="poster-thumb"
                  style={{
                    width: 72,
                    height: 100,
                    background: `linear-gradient(135deg, hsl(${hueOf(detailTarget.id)} 42% 26%), hsl(${(hueOf(detailTarget.id) + 45) % 360} 52% 10%))`,
                  }}
                >
                  {(detailTarget.nameCn || detailTarget.name).slice(0, 1)}
                </span>
              )}
              <span className="subject-name">
                <b>{detailTarget.nameCn || detailTarget.name}</b>
                <span>{detailTarget.name}</span>
                <span className="panel-note" style={{ marginTop: 4 }}>
                  #ID {detailTarget.id} · Bangumi {detailTarget.bangumiId ?? '-'}
                </span>
              </span>
            </div>

            <Descriptions
              bordered
              size="small"
              column={2}
              items={[
                { key: 'type', label: '类型', children: <span className="type-chip">{typeLabel[detailTarget.type] ?? `类型 ${detailTarget.type}`}</span> },
                { key: 'airDate', label: '放送日期', children: detailTarget.airDate || '-' },
                { key: 'eps', label: '总集数', children: detailTarget.eps ?? '-' },
                { key: 'volumes', label: '卷数', children: detailTarget.volumes ?? '-' },
                { key: 'nsfw', label: 'NSFW', children: detailTarget.nsfw ? <Tag color="red">是</Tag> : <Tag>否</Tag> },
                { key: 'score', label: '评分', children: detailTarget.score > 0 ? Number(detailTarget.score).toFixed(1) : '-' },
                { key: 'rank', label: '排名', children: detailTarget.rank > 0 ? `#${detailTarget.rank}` : '-' },
                { key: 'collection', label: '收藏数', children: Number(detailTarget.collectionTotal ?? 0).toLocaleString() },
                { key: 'createdAt', label: '创建时间', children: detailTarget.createdAt ?? '-' },
                { key: 'updatedAt', label: '更新时间', children: detailTarget.updatedAt ?? '-' },
              ]}
            />

            <section className="panel" style={{ padding: 12 }}>
              <h4 className="panel-title">简介</h4>
              <p style={{ marginTop: 8, color: 'var(--text-soft)', fontSize: 13, lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>
                {detailTarget.summary || '-'}
              </p>
            </section>

            <section className="panel" style={{ padding: 12 }}>
              <h4 className="panel-title">标签</h4>
              <div className="chip-row" style={{ marginTop: 8 }}>
                {(detailTarget.tags ?? []).map((tag) => (
                  <span key={tag.id} className="subject-chip">
                    {tag.name} · {tag.count}
                  </span>
                ))}
                {(detailTarget.tags ?? []).length === 0 && <span className="cell-muted">暂无标签</span>}
              </div>
            </section>

            <section className="panel" style={{ padding: 12 }}>
              <h4 className="panel-title">关联条目</h4>
              <div className="chip-row" style={{ marginTop: 8 }}>
                {(detailTarget.relations ?? []).map((rel, index) => (
                  <span key={`${rel.relation}-${index}`} className="subject-chip">
                    {rel.relation} → {rel.relatedSubject?.nameCn || rel.relatedSubject?.name || `#${rel.relatedSubject?.id}`}
                  </span>
                ))}
                {(detailTarget.relations ?? []).length === 0 && <span className="cell-muted">暂无关联</span>}
              </div>
            </section>

            <section className="panel table-panel">
              <div className="panel-head">
                <div>
                  <h4 className="panel-title">剧集列表</h4>
                  <div className="panel-sub">GET /api/client/subjects/{detailTarget.id}/episodes</div>
                </div>
                <span className="panel-note">共 {detailEpisodes.length} 集</span>
              </div>
              <Table<EpisodeVO>
                rowKey="id"
                size="small"
                dataSource={detailEpisodes}
                pagination={false}
                scroll={{ x: 680 }}
                columns={[
                  { title: '序号', dataIndex: 'sort', width: 64, className: 'num', render: (v) => Number(v ?? 0).toLocaleString() },
                  { title: '标题', render: (_, ep) => <span className="subject-name"><b>{ep.nameCn || ep.name || '-'}</b>{ep.nameCn && ep.name ? <span>{ep.name}</span> : null}</span> },
                  { title: '类型', dataIndex: 'type', width: 76, render: (v: number) => <span className="type-chip">{episodeTypeLabel[v] ?? `类型 ${v}`}</span> },
                  { title: '放送日', dataIndex: 'airdate', width: 104, className: 'num', render: (v) => v || '-' },
                  { title: '时长', dataIndex: 'duration', width: 80, className: 'num', render: (v) => v || '-' },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    width: 96,
                    render: (v: string) => {
                      const meta = episodeStatusMeta[v] ?? { label: v || '-', cls: 'neutral' };
                      return (
                        <span className={`status-tag ${meta.cls}`}>
                          <span className="status-dot" />
                          {meta.label}
                        </span>
                      );
                    },
                  },
                ]}
              />
            </section>
          </div>
        )}
      </Drawer>
    </div>
  );
}
