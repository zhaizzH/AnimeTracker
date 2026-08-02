import { useState } from 'react';
import { Badge, Avatar, Button, Modal, Form, Input, Upload, message } from 'antd';
import { UserOutlined, EditOutlined, KeyOutlined, MailOutlined } from '@ant-design/icons';
import { useQuery, useMutation } from '@tanstack/react-query';
import { userApi } from '@/api/user';
import { commonApi } from '@/api/common';
import { useAuthStore } from '@/store/authStore';
import PageHeading from '@/components/PageHeading';
import type { UpdateUserDTO, ChangePasswordDTO } from '@/types';

export default function Profile() {
  const { user, setUser } = useAuthStore();
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [emailModalOpen, setEmailModalOpen] = useState(false);

  const { data: profile, refetch } = useQuery({
    queryKey: ['profile'],
    queryFn: () => userApi.profile(),
  });

  const displayUser = profile || user;

  const updateMutation = useMutation({
    mutationFn: (data: UpdateUserDTO) => userApi.update(data),
    onSuccess: (result: any) => {
      setUser(result);
      refetch();
      message.success('资料已更新');
      setEditModalOpen(false);
    },
    onError: (err: any) => message.error(err.message || '更新失败'),
  });

  const passwordMutation = useMutation({
    mutationFn: (data: ChangePasswordDTO) => userApi.changePassword(data),
    onSuccess: () => {
      message.success('密码已修改');
      setPasswordModalOpen(false);
    },
    onError: (err: any) => message.error(err.message || '修改失败'),
  });

  const handleUpload = async (file: File) => {
    try {
      const url = await commonApi.upload(file, 'avatar');
      updateMutation.mutate({ avatar: url });
    } catch {
      message.error('上传失败');
    }
  };

  const handleEmailChangeSuccess = () => {
    refetch();
    setEmailModalOpen(false);
  };

  return (
    <div>
      <PageHeading
        index="05 / PROFILE"
        title="个人档案"
        subtitle={`@${displayUser?.username || ''} · 本子上的记录`}
      />

      <div className="profile-sheet">
        <div className="profile-head">
          <Badge
            count={
              <Upload showUploadList={false} beforeUpload={file => { handleUpload(file); return false; }}>
                <EditOutlined
                  style={{
                    fontSize: 16,
                    color: '#fff',
                    background: 'var(--accent)',
                    borderRadius: '50%',
                    padding: 4,
                  }}
                />
              </Upload>
            }
            offset={[-8, 66]}
          >
            <Avatar size={84} src={displayUser?.avatar} icon={<UserOutlined />} />
          </Badge>
          <div>
            <h2>{displayUser?.nickname || displayUser?.username}</h2>
            <p>USER / {displayUser?.username}</p>
          </div>
        </div>

        <dl className="dossier-meta">
          <div><dt>用户名</dt><dd>{displayUser?.username}</dd></div>
          <div><dt>邮箱</dt><dd>{displayUser?.email}</dd></div>
          <div><dt>角色</dt><dd>{displayUser?.role === 'ADMIN' ? '管理员' : '用户'}</dd></div>
          <div><dt>注册时间</dt><dd>{displayUser?.createdAt}</dd></div>
        </dl>

        <div className="profile-actions">
          <Button icon={<EditOutlined />} onClick={() => setEditModalOpen(true)} block>
            编辑资料
          </Button>
          <Button icon={<KeyOutlined />} onClick={() => setPasswordModalOpen(true)} block>
            修改密码
          </Button>
          <Button icon={<MailOutlined />} onClick={() => setEmailModalOpen(true)} block>
            修改邮箱
          </Button>
        </div>
      </div>

      <Modal title="编辑资料" open={editModalOpen} onCancel={() => setEditModalOpen(false)} footer={null}>
        <Form
          layout="vertical"
          initialValues={{ nickname: displayUser?.nickname || '' }}
          onFinish={values => updateMutation.mutate(values)}
        >
          <Form.Item name="nickname" label="昵称" rules={[{ max: 64 }]}>
            <Input placeholder="输入昵称" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={updateMutation.isPending} block>
              保存
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="修改密码" open={passwordModalOpen} onCancel={() => setPasswordModalOpen(false)} footer={null}>
        <Form layout="vertical" onFinish={values => passwordMutation.mutate(values)}>
          <Form.Item name="oldPassword" label="当前密码" rules={[{ required: true }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="newPassword" label="新密码" rules={[{ required: true, min: 6, max: 128 }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={passwordMutation.isPending} block>
              修改
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="修改邮箱" open={emailModalOpen} onCancel={() => setEmailModalOpen(false)} footer={null}>
        <EmailChangeForm onSuccess={handleEmailChangeSuccess} />
      </Modal>
    </div>
  );
}

function EmailChangeForm({ onSuccess }: { onSuccess?: () => void }) {
  const [step, setStep] = useState<'send' | 'verify'>('send');
  const [newEmail, setNewEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const sendCode = async (values: { newEmail: string }) => {
    setLoading(true);
    try {
      await userApi.sendEmailCode(values.newEmail);
      setNewEmail(values.newEmail);
      setStep('verify');
      message.success('验证码已发送');
    } catch (err: any) {
      message.error(err.message || '发送失败');
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async (values: { code: string }) => {
    setLoading(true);
    try {
      await userApi.verifyEmailCode(newEmail, values.code);
      message.success('邮箱已修改');
      setStep('send');
      onSuccess?.();
    } catch (err: any) {
      message.error(err.message || '验证失败');
    } finally {
      setLoading(false);
    }
  };

  if (step === 'send') {
    return (
      <Form layout="vertical" onFinish={sendCode}>
        <Form.Item name="newEmail" label="新邮箱" rules={[{ required: true, type: 'email' }]}>
          <Input placeholder="输入新邮箱地址" />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading} block>发送验证码</Button>
        </Form.Item>
      </Form>
    );
  }

  return (
    <Form layout="vertical" onFinish={verifyCode}>
      <p>验证码已发送至 <strong>{newEmail}</strong></p>
      <Form.Item name="code" label="6位验证码" rules={[{ required: true, len: 6 }]}>
        <Input placeholder="输入验证码" maxLength={6} />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading} block>确认修改</Button>
      </Form.Item>
    </Form>
  );
}
