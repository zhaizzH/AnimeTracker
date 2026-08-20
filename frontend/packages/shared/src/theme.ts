import type { ThemeConfig } from 'antd';

// 清新杂志感：暖纸白底、植物墨绿主色、衬线标题 + 无衬线正文，克制的留白。
export const antdTheme: ThemeConfig = {
  token: {
    colorPrimary: '#4A6B54',
    colorPrimaryHover: '#62866E',
    colorPrimaryActive: '#3C5C46',
    colorInfo: '#4A6B54',
    colorSuccess: '#5B8C5A',
    colorWarning: '#B58A3C',
    colorError: '#B3564A',
    colorTextBase: '#23261F',
    colorText: '#23261F',
    colorTextSecondary: '#6E7266',
    colorTextTertiary: '#A2A69A',
    colorTextQuaternary: '#C4C8BC',
    colorBgLayout: '#F7F5F0',
    colorBgContainer: '#FFFFFF',
    colorBgElevated: '#FFFFFF',
    colorBorder: '#E3E0D7',
    colorBorderSecondary: '#ECE9E1',
    colorSplit: '#ECE9E1',
    borderRadius: 10,
    fontFamily: "'Noto Sans SC','PingFang SC','Microsoft YaHei',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
    controlHeight: 38,
  },
  components: {
    Layout: {
      headerBg: '#FFFFFF',
      bodyBg: '#F7F5F0',
    },
    Menu: {
      itemBg: 'transparent',
      itemColor: '#6E7266',
      itemHoverColor: '#4A6B54',
      itemSelectedColor: '#4A6B54',
      horizontalItemSelectedColor: '#4A6B54',
    },
    Button: {
      defaultBg: '#FFFFFF',
      defaultBorderColor: '#E3E0D7',
      defaultHoverBorderColor: '#4A6B54',
      defaultHoverColor: '#4A6B54',
    },
    Card: {
      headerBg: 'transparent',
    },
    Tabs: {
      itemSelectedColor: '#4A6B54',
      inkBarColor: '#4A6B54',
      itemHoverColor: '#4A6B54',
    },
    Table: {
      headerBg: '#F4F2EC',
      headerColor: '#4A4E45',
      rowHoverBg: '#F7F5F0',
    },
    Tag: {
      defaultBg: '#F2F0EA',
      defaultColor: '#4A4E45',
    },
    Statistic: {
      contentFontSize: 28,
    },
  },
};
