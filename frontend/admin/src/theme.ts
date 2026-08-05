import type { ThemeConfig } from 'antd';
import { theme } from 'antd';

export const antdTheme: ThemeConfig = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#00b3a4',
    colorInfo: '#2f7fe8',
    colorSuccess: '#1f9d6f',
    colorWarning: '#e99b2f',
    colorError: '#d84a3f',
    colorBgBase: '#f4f7fa',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#eef2f6',
    colorBorder: '#dfe6ee',
    colorBorderSecondary: '#e7edf3',
    colorText: '#17232e',
    colorTextSecondary: '#5b6b79',
    colorTextTertiary: '#8a9aa8',
    borderRadius: 6,
    fontSize: 14,
    controlHeight: 34,
    fontFamily: '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Segoe UI", sans-serif',
  },
  components: {
    Button: {
      primaryShadow: 'none',
      defaultBg: '#ffffff',
      defaultBorderColor: '#c8d3de',
      defaultColor: '#17232e',
    },
    Input: {
      activeShadow: '0 0 0 2px rgba(0,179,164,0.12)',
    },
    Layout: {
      bodyBg: '#eef2f6',
      headerBg: 'rgba(255,255,255,0.92)',
      siderBg: '#ffffff',
    },
    Menu: {
      itemBg: '#ffffff',
      itemSelectedBg: 'rgba(0,179,164,0.10)',
      itemSelectedColor: '#00a89c',
    },
    Segmented: {
      itemSelectedBg: '#ffffff',
      itemSelectedColor: '#00a89c',
    },
    Table: {
      headerBg: '#f6f8fb',
      rowHoverBg: 'rgba(0,179,164,0.05)',
      borderColor: '#dfe6ee',
    },
  },
};
