// 原型假数据。不请求任何接口。
export const ALL = '__all__';

export type Anime = {
  id: number;
  title: string;
  year: number;
  score: number;
  eps: number;
  weekday: string;
  hue: number;
};

export const ANIME: Anime[] = [
  { id: 1, title: '孤独摇滚', year: 2022, score: 8.7, eps: 12, weekday: '周六', hue: 20 },
  { id: 2, title: '葬送的芙莉莲', year: 2023, score: 9.1, eps: 28, weekday: '周五', hue: 250 },
  { id: 3, title: '进击的巨人', year: 2013, score: 9.0, eps: 25, weekday: '周日', hue: 30 },
  { id: 4, title: '鬼灭之刃', year: 2019, score: 8.2, eps: 26, weekday: '周六', hue: 10 },
  { id: 5, title: '咒术回战', year: 2020, score: 8.4, eps: 24, weekday: '周五', hue: 280 },
  { id: 6, title: '赛马娘', year: 2021, score: 8.6, eps: 13, weekday: '周日', hue: 330 },
  { id: 7, title: '辉夜大小姐想让我告白', year: 2019, score: 8.9, eps: 12, weekday: '周六', hue: 350 },
  { id: 8, title: '间谍过家家', year: 2022, score: 8.5, eps: 12, weekday: '周六', hue: 140 },
  { id: 9, title: '电锯人', year: 2022, score: 8.3, eps: 12, weekday: '周二', hue: 35 },
  { id: 10, title: '紫罗兰永恒花园', year: 2018, score: 8.8, eps: 13, weekday: '周三', hue: 210 },
  { id: 11, title: '轻音少女', year: 2009, score: 8.7, eps: 13, weekday: '周四', hue: 55 },
  { id: 12, title: '吹响！上低音号', year: 2015, score: 8.8, eps: 13, weekday: '周二', hue: 170 },
];

// agent 导航到「2022 年」时展示的名单，与全量明显不同，肉眼可验证筛选生效。
export const ANIME_2022: Anime[] = [
  { id: 101, title: '孤独摇滚', year: 2022, score: 8.7, eps: 12, weekday: '周六', hue: 20 },
  { id: 102, title: '莉可丽丝', year: 2022, score: 8.1, eps: 13, weekday: '周六', hue: 320 },
  { id: 103, title: '电锯人', year: 2022, score: 8.3, eps: 12, weekday: '周二', hue: 35 },
  { id: 104, title: '间谍过家家', year: 2022, score: 8.5, eps: 12, weekday: '周六', hue: 140 },
  { id: 105, title: '来自深渊 烈日的黄金乡', year: 2022, score: 8.6, eps: 12, weekday: '周三', hue: 190 },
  { id: 106, title: '夏日重现', year: 2022, score: 8.4, eps: 25, weekday: '周四', hue: 195 },
  { id: 107, title: '赛博朋克：边缘行者', year: 2022, score: 8.9, eps: 10, weekday: '周二', hue: 300 },
  { id: 108, title: '异世界舅舅', year: 2022, score: 8.2, eps: 13, weekday: '周三', hue: 100 },
];

export const TABS = [
  { key: 'want', label: '想看' },
  { key: 'watched', label: '看过' },
  { key: 'watching', label: '在看' },
  { key: 'paused', label: '搁置' },
  { key: 'dropped', label: '抛弃' },
];

export const COLLECTIONS: Record<string, Anime[]> = {
  want: [
    { id: 201, title: '葬送的芙莉莲', year: 2023, score: 9.1, eps: 28, weekday: '周五', hue: 250 },
    { id: 202, title: '紫罗兰永恒花园', year: 2018, score: 8.8, eps: 13, weekday: '周三', hue: 210 },
    { id: 203, title: '辉夜大小姐想让我告白', year: 2019, score: 8.9, eps: 12, weekday: '周六', hue: 350 },
  ],
  watched: [
    { id: 301, title: '进击的巨人', year: 2013, score: 9.0, eps: 25, weekday: '周日', hue: 30 },
    { id: 302, title: '轻音少女', year: 2009, score: 8.7, eps: 13, weekday: '周四', hue: 55 },
  ],
  watching: [
    { id: 401, title: '咒术回战', year: 2020, score: 8.4, eps: 24, weekday: '周五', hue: 280 },
    { id: 402, title: '吹响！上低音号', year: 2015, score: 8.8, eps: 13, weekday: '周二', hue: 170 },
    { id: 403, title: '赛马娘', year: 2021, score: 8.6, eps: 13, weekday: '周日', hue: 330 },
  ],
  paused: [
    { id: 501, title: '鬼灭之刃', year: 2019, score: 8.2, eps: 26, weekday: '周六', hue: 10 },
  ],
  dropped: [],
};

export const WANT_ADDITION: Anime = {
  id: 601,
  title: '孤独摇滚',
  year: 2022,
  score: 8.7,
  eps: 12,
  weekday: '周六',
  hue: 20,
};

export const YEARS = ['2024', '2023', '2022', '2021', '2020', '2019', '2018', '2015', '2013', '2009'];
export const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
