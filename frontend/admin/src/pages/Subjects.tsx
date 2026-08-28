import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, Form, Input, InputNumber, Modal, Popconfirm, Select, Space, Table, message } from 'antd';
import { adminSubjectsApi, subjectsApi, tagsApi } from '@shared';

type SubjectFilters = { q?: string; tag?: string[]; scoreMin?: number; scoreMax?: number; year?: number; weekday?: number };
const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

export default function Subjects() {
  const qc = useQueryClient();
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<SubjectFilters>({});
  const setFilter = (patch: Partial<SubjectFilters>) => { setFilters((f) => ({ ...f, ...patch })); setPage(1); };
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const [form] = Form.useForm();
  const { data: tags } = useQuery({ queryKey: ['tags'], queryFn: tagsApi.list, staleTime: 60_000 });
  const { data: years } = useQuery({ queryKey: ['subject-years'], queryFn: subjectsApi.years, staleTime: 60_000 });
  const { data, isLoading } = useQuery({ queryKey: ['admin-subjects', filters, page], queryFn: () => subjectsApi.search({ ...filters, page, size: 20, sort: 'score', order: 'desc' }) });
  const inval = () => { qc.invalidateQueries({ queryKey: ['admin-subjects'] }); };
  const openCreate = () => { setEditing(null); form.resetFields(); setOpen(true); };
  const openEdit = (id: number, rec: Partial<adminSubjectsApi.SubjectForm>) => { setEditing(id); form.setFieldsValue(rec); setOpen(true); };
  const save = useMutation({
    mutationFn: async (v: adminSubjectsApi.SubjectForm) => { if (editing) await adminSubjectsApi.update(editing, v); else await adminSubjectsApi.create(v); },
    onSuccess: () => { message.success('已保存'); setOpen(false); inval(); }, onError: (e) => message.error((e as Error).message),
  });
  const del = useMutation({ mutationFn: (id: number) => adminSubjectsApi.remove(id), onSuccess: () => { message.success('已删除'); inval(); } });
  return (
    <div>
      <Space wrap style={{ marginBottom: 16 }}>
        <Input.Search placeholder="搜索番剧" allowClear onSearch={(v) => setFilter({ q: v.trim() || undefined })} style={{ width: 220 }} />
        <Select mode="multiple" allowClear placeholder="标签" options={(tags ?? []).map((t) => ({ value: t.name, label: t.name }))} style={{ minWidth: 160 }} maxTagCount="responsive" onChange={(v) => setFilter({ tag: v.length ? v : undefined })} />
        <InputNumber min={0} max={10} step={0.1} precision={1} placeholder="最低评分" onChange={(v) => setFilter({ scoreMin: v ?? undefined })} />
        <InputNumber min={0} max={10} step={0.1} precision={1} placeholder="最高评分" onChange={(v) => setFilter({ scoreMax: v ?? undefined })} />
        <Select allowClear placeholder="年份" options={(years ?? []).map((y) => ({ value: y, label: y }))} style={{ width: 110 }} onChange={(v) => setFilter({ year: v ?? undefined })} />
        <Select allowClear placeholder="星期" options={WEEKDAYS.map((w, i) => ({ value: i, label: w }))} style={{ width: 110 }} onChange={(v) => setFilter({ weekday: v ?? undefined })} />
        <Button type="primary" onClick={openCreate}>新建番剧</Button>
      </Space>
      <Table rowKey="id" loading={isLoading} dataSource={(data?.content ?? []) as unknown as Record<string, unknown>[]} pagination={{ current: page, total: data?.total, pageSize: 20, onChange: setPage }} columns={[
        { title: 'ID', dataIndex: 'id', width: 60 },
        { title: '封面', dataIndex: 'image', width: 50, render: (v: string) => v ? <img src={v} alt="" style={{ width: 36, aspectRatio: '3/4', objectFit: 'cover' }} /> : null },
        { title: '中文名', dataIndex: 'nameCn' }, { title: '原名', dataIndex: 'name' }, { title: '评分', dataIndex: 'score', width: 80 },
        { title: '集数', dataIndex: 'eps', width: 70 },
        { title: '操作', width: 160, render: (_: unknown, r: Record<string, unknown>) => (
          <Space>
            <Button size="small" onClick={() => openEdit(Number(r.id), r)}>编辑</Button>
            <Popconfirm title="确定删除？" onConfirm={() => del.mutate(Number(r.id))}><Button size="small" danger>删除</Button></Popconfirm>
          </Space>
        ) },
      ]} />
      <Modal open={open} title={editing ? '编辑番剧' : '新建番剧'} onCancel={() => setOpen(false)} onOk={() => form.submit()} destroyOnHidden>
        <Form form={form} layout="vertical" onFinish={(v) => save.mutate(v)}>
          {!editing && <Form.Item name="bangumiId" label="Bangumi ID" rules={[{ required: true }]}><InputNumber aria-label="Bangumi ID" style={{ width: '100%' }} /></Form.Item>}
          <Form.Item name="name" label="日文/英文名" rules={[{ required: true }]}><Input aria-label="日文/英文名" /></Form.Item>
          <Form.Item name="nameCn" label="中文名"><Input aria-label="中文名" /></Form.Item>
          <Form.Item name="summary" label="简介"><Input.TextArea rows={4} aria-label="简介" /></Form.Item>
          <Form.Item name="type" label="类型" initialValue={2}><InputNumber aria-label="类型" min={1} /></Form.Item>
          <Form.Item name="eps" label="总集数"><InputNumber aria-label="总集数" min={0} /></Form.Item>
          <Form.Item name="airDate" label="播出日期"><Input aria-label="播出日期" placeholder="2026-04-01" /></Form.Item>
          <Form.Item name="image" label="封面 URL"><Input aria-label="封面 URL" /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
