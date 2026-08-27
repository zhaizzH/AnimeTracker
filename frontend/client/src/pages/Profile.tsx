import { useQuery } from '@tanstack/react-query';
import { Avatar, Button, Card, Descriptions, Form, Input, Modal, Space, Upload, message, theme } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi, filesApi, useAuthStore, formatDate, publishSignedOut } from '@shared';

export default function Profile() {
  const { token } = theme.useToken();
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const { data } = useQuery({ queryKey: ['me'], queryFn: () => authApi.me() });
  const u = data ?? user;
  const [pwdOpen, setPwdOpen] = useState(false);
  const [pwdForm] = Form.useForm();
  const [emailOpen, setEmailOpen] = useState(false);
  const [emailForm] = Form.useForm();
  const [emailStep, setEmailStep] = useState<'send' | 'verify'>('send');
  const [editOpen, setEditOpen] = useState(false);
  const [editForm] = Form.useForm();

  const onPwd = async () => {
    const v = await pwdForm.validateFields();
    await authApi.updatePassword({ oldPassword: v.oldPassword, newPassword: v.newPassword });
    useAuthStore.getState().setUnauthenticated();
    publishSignedOut();
    message.success('密码已修改'); setPwdOpen(false); pwdForm.resetFields();
    navigate('/login');
  };
  const onSendCode = async () => {
    const v = await emailForm.validateFields(['newEmail']);
    await authApi.sendEmailCode({ newEmail: v.newEmail });
    message.success('验证码已发送至新邮箱'); setEmailStep('verify');
  };
  const onVerifyEmail = async () => {
    const v = await emailForm.validateFields();
    await authApi.verifyEmailCode({ newEmail: v.newEmail, code: v.code });
    message.success('邮箱已更新'); setEmailOpen(false); emailForm.resetFields(); setEmailStep('send');
  };
  const onEdit = async () => {
    const v = await editForm.validateFields();
    const next = await authApi.updateProfile({ nickname: v.nickname, avatar: v.avatar });
    useAuthStore.setState({ user: next }); setEditOpen(false); message.success('资料已更新');
  };
  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: 24 }}>
      <Card className="od-glass-card">
        <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          <Avatar size={80} src={u?.avatar ?? undefined} style={{ background: token.colorPrimary }}>{u?.nickname ?? u?.username?.slice(0, 1)}</Avatar>
          <div>
            <h2 style={{ marginBottom: 4 }}>{u?.nickname ?? u?.username}</h2>
            <Descriptions column={1} size="small" items={[
              { key: 'u', label: '用户名', children: u?.username },
              { key: 'e', label: '邮箱', children: u?.email },
              { key: 'r', label: '角色', children: u?.role },
              { key: 'c', label: '注册时间', children: formatDate(u?.createdAt) },
            ]} />
            <Space style={{ marginTop: 8 }}>
              <Button onClick={() => { editForm.setFieldsValue({ nickname: u?.nickname, avatar: u?.avatar }); setEditOpen(true); }}>编辑资料</Button>
              <Button onClick={() => setPwdOpen(true)}>修改密码</Button>
              <Button onClick={() => setEmailOpen(true)}>修改邮箱</Button>
            </Space>
          </div>
        </div>
      </Card>

      <Modal open={pwdOpen} title="修改密码" okText="确认" onCancel={() => setPwdOpen(false)} onOk={onPwd} destroyOnHidden>
        <Form form={pwdForm} layout="vertical">
          <Form.Item name="oldPassword" label="旧密码" rules={[{ required: true }]}><Input.Password aria-label="旧密码" autoComplete="current-password" /></Form.Item>
          <Form.Item name="newPassword" label="新密码" rules={[{ required: true, min: 6 }]}><Input.Password aria-label="新密码" autoComplete="new-password" /></Form.Item>
        </Form>
      </Modal>

      <Modal open={emailOpen} title="修改邮箱" okText="确认" onCancel={() => { setEmailOpen(false); setEmailStep('send'); }} onOk={emailStep === 'send' ? onSendCode : onVerifyEmail} destroyOnHidden>
        <Form form={emailForm} layout="vertical">
          <Form.Item name="newEmail" label="新邮箱" rules={[{ required: true, type: 'email' }]}><Input aria-label="新邮箱" autoComplete="email" spellCheck={false} inputMode="email" /></Form.Item>
          {emailStep === 'verify' && <Form.Item name="code" label="验证码" rules={[{ required: true, len: 6 }]}><Input aria-label="验证码" maxLength={6} inputMode="numeric" spellCheck={false} /></Form.Item>}
        </Form>
      </Modal>

      <Modal open={editOpen} title="编辑资料" okText="确认" onCancel={() => setEditOpen(false)} onOk={onEdit} destroyOnHidden>
        <Form form={editForm} layout="vertical">
          <Form.Item name="nickname" label="昵称" rules={[{ max: 64 }]}><Input aria-label="昵称" autoComplete="off" /></Form.Item>
          <Form.Item name="avatar" label="头像">
            <Input aria-label="头像" autoComplete="off" />
          </Form.Item>
          <Upload accept="image/jpeg,image/png,image/webp" showUploadList={false} customRequest={async ({ file, onSuccess, onError }) => {
            try { const url = await filesApi.uploadAvatar(file as File); editForm.setFieldValue('avatar', url); onSuccess?.(url); message.success('已上传'); }
            catch (e) { onError?.(e as Error); }
          }}><Button icon={<UploadOutlined />}>上传头像</Button></Upload>
        </Form>
      </Modal>
    </div>
  );
}
