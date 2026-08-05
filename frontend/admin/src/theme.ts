import type { ThemeConfig } from 'antd';
import { theme } from 'antd';

const fontFamily =
  '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Segoe UI", sans-serif';

export const lightTheme: ThemeConfig = {
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
    fontFamily,
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

export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#2fd6c8',
    colorInfo: '#62a6f4',
    colorSuccess: '#3dbb8a',
    colorWarning: '#f2b04c',
    colorError: '#ef6a60',
    colorBgBase: '#0b1216',
    colorBgContainer: '#141e24',
    colorBgElevated: '#1a262e',
    colorBgLayout: '#0b1216',
    colorBorder: '#26343e',
    colorBorderSecondary: '#1d2a32',
    colorText: '#e6edf1',
    colorTextSecondary: '#a9b8c2',
    colorTextTertiary: '#71828d',
    borderRadius: 6,
    fontSize: 14,
    controlHeight: 34,
    fontFamily,
  },
  components: {
    Button: {
      primaryShadow: 'none',
      defaultBg: '#141e24',
      defaultBorderColor: '#33424e',
      defaultColor: '#dce6eb',
    },
    Input: {
      activeShadow: '0 0 0 2px rgba(45,212,199,0.16)',
    },
    Layout: {
      bodyBg: '#0b1216',
      headerBg: 'rgba(11,18,22,0.92)',
      siderBg: '#101a20',
    },
    Menu: {
      itemBg: '#101a20',
      itemSelectedBg: 'rgba(45,212,199,0.14)',
      itemSelectedColor: '#2fd6c8',
    },
    Segmented: {
      itemSelectedBg: '#1a262e',
      itemSelectedColor: '#2fd6c8',
    },
    Table: {
      headerBg: '#18232a',
      rowHoverBg: 'rgba(45,212,199,0.07)',
      borderColor: '#26343e',
    },
  },
};
