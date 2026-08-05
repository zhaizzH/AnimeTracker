import { Button, Dropdown, Tooltip } from 'antd';
import { DesktopOutlined, MoonOutlined, SunOutlined } from '@ant-design/icons';
import type { ReactNode } from 'react';
import { useThemeStore, type ThemeMode } from '../store/themeStore';

const options = [
  { key: 'light', label: '浅色', icon: <SunOutlined /> },
  { key: 'dark', label: '深色', icon: <MoonOutlined /> },
  { key: 'system', label: '跟随系统', icon: <DesktopOutlined /> },
] as const;

const modeIcon: Record<ThemeMode, ReactNode> = {
  light: <SunOutlined />,
  dark: <MoonOutlined />,
  system: <DesktopOutlined />,
};

export default function ThemeToggle() {
  const mode = useThemeStore((s) => s.mode);
  const setMode = useThemeStore((s) => s.setMode);

  return (
    <Tooltip title="主题模式">
      <Dropdown
        menu={{
          items: options.map((option) => ({
            key: option.key,
            label: option.label,
            icon: option.icon,
          })),
          selectable: true,
          selectedKeys: [mode],
          onClick: ({ key }) => setMode(key as ThemeMode),
        }}
        trigger={['click']}
        placement="bottomRight"
      >
        <Button type="text" icon={modeIcon[mode]} aria-label="切换主题" />
      </Dropdown>
    </Tooltip>
  );
}
