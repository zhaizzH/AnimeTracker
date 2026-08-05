import { useCallback, useEffect, useMemo, useState } from 'react';
import { App, Button, Segmented, Tooltip } from 'antd';
import {
  HeartOutlined,
  LoginOutlined,
  PlaySquareOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  UserAddOutlined,
  UserOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons';
import BarList from '../components/BarList';
import DonutChart from '../components/DonutChart';
import StatCard from '../components/StatCard';
import TrendChart from '../components/TrendChart';
import { dashboardApi } from '../api/dashboard';
import { importsApi } from '../api/imports';
import type {
  CollectionStatsVO,
  DashboardOverviewVO,
  HotSubjectVO,
  ImportRecordVO,
  ImportStatusVO,
  SubjectStatsVO,
  TrendPointVO,
} from '../types/api';

const typeLabel: Record<number, string> = {
  1: '想看',
  2: '在看',
  3: '看过',
  4: '搁置',
  5: '抛弃',
};

const typeColor: Record<number, string> = {
  1: 'var(--amber)',
  2: 'var(--blue)',
  3: 'var(--cyan)',
  4: 'var(--text-faint)',
  5: 'var(--red)',
};

const seasonColor: Record<string, string> = {
  winter: 'var(--blue)',
  spring: 'var(--cyan)',
  summer: 'var(--amber)',
  autumn: 'var(--purple)',
};

function hueOf(id: number): number {
  return Math.abs(Math.sin(id * 12.9898) * 43758.5453) % 360;
}

function seasonLabel(key: string): string {
  const [year, season] = key.split('-');
  const seasonCn: Record<string, string> = {
    winter: '冬',
    spring: '春',
    summer: '夏',
    autumn: '秋',
  };
  return season && seasonCn[season] ? `${year} ${seasonCn[season]}` : key;
}

function seasonHue(key: string): string {
  const season = key.split('-')[1] ?? '';
  return seasonColor[season] ?? 'var(--text-faint)';
}

const emptyOverview: DashboardOverviewVO = {
  userCount: 0,
  subjectCount: 0,
  collectionCount: 0,
  episodeCount: 0,
  importCount: 0,
  todayNewUsers: 0,
  todayNewCollections: 0,
  todayLogins: 0,
};

const emptyImportStatus: ImportStatusVO = {
  lastImportedAt: null,
  totalSubjects: 0,
  recentRecords: [],
};

const statusLabel: Record<string, string> = {
  RUNNING: '运行中',
  COMPLETED: '已完成',
  FAILED: '失败',
};

export default function Dashboard() {
  const { message } = App.useApp();
  const [range, setRange] = useState<7 | 30>(7);
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<DashboardOverviewVO>(emptyOverview);
  const [trends, setTrends] = useState<TrendPointVO[]>([]);
  const [collectionStats, setCollectionStats] = useState<CollectionStatsVO>({
    types: [],
    ratings: [],
  });
  const [subjectStats, setSubjectStats] = useState<SubjectStatsVO>({
    seasons: [],
    importStatuses: [],
    importStat: { importTotal: 0, importSucceeded: 0, importFailed: 0 },
  });
  const [hotSubjects, setHotSubjects] = useState<HotSubjectVO[]>([]);
  const [importStatus, setImportStatus] = useState<ImportStatusVO>(emptyImportStatus);

  const load = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true);
      try {
        const [ov, trend, collection, subject, hot, importInfo] = await Promise.all([
          dashboardApi.overview(),
          dashboardApi.trends(range),
          dashboardApi.collectionStats(),
          dashboardApi.subjectStats(),
          dashboardApi.hot(5),
          importsApi.status(),
        ]);
        setOverview(ov ?? emptyOverview);
        setTrends(
          (trend ?? []).map((point) => ({
            ...point,
            date: String(point.date).slice(5),
          })),
        );
        setCollectionStats(collection ?? { types: [], ratings: [] });
        setSubjectStats(subject ?? { seasons: [], importStatuses: [], importStat: { importTotal: 0, importSucceeded: 0, importFailed: 0 } });
        setHotSubjects(hot ?? []);
        setImportStatus(importInfo ?? emptyImportStatus);
      } catch (error) {
        if (!silent) message.error(error instanceof Error ? error.message : '看板数据加载失败');
      } finally {
        if (!silent) setLoading(false);
      }
    },
    [message, range],
  );

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range]);

  const collectionItems = useMemo(
    () =>
      (collectionStats.types ?? []).map((item) => ({
        label: typeLabel[item.type] ?? `类型 ${item.type}`,
        value: item.count,
        color: typeColor[item.type] ?? 'var(--text-faint)',
      })),
    [collectionStats],
  );
  const seasonItems = useMemo(
    () =>
      (subjectStats.seasons ?? []).map((item) => ({
        label: seasonLabel(item.seasonKey),
        value: item.count,
        color: seasonHue(item.seasonKey),
      })),
    [subjectStats],
  );
  const importStatusItems = useMemo(
    () =>
      (subjectStats.importStatuses ?? []).map((item) => ({
        label: item.importStatus === 1 ? '已导入' : '待导入',
        value: item.count,
        color: item.importStatus === 1 ? 'var(--green)' : 'var(--text-faint)',
      })),
    [subjectStats],
  );
  const ratings = collectionStats.ratings ?? [];
  const records = importStatus.recentRecords ?? [];

  const maxScore = Math.max(1, ...ratings.map((r) => r.count));
  const maxHot = Math.max(1, ...hotSubjects.map((h) => h.collectionCount));
  const collectionTotal = collectionItems.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="dash-stack">
      <div className="dash-toolbar">
        <div>
          <div className="dash-toolbar-sub">接口 · /api/admin/dashboard/* · 每 5 分钟自动同步</div>
        </div>
        <div className="dash-toolbar-actions">
          <Segmented
            options={[
              { label: '近 7 日', value: 7 },
              { label: '近 30 日', value: 30 },
            ]}
            value={range}
            onChange={(value) => setRange(value as 7 | 30)}
          />
          <Tooltip title="刷新看板数据">
            <Button icon={<ReloadOutlined spin={loading} />} onClick={() => load()} />
          </Tooltip>
        </div>
      </div>

      <div className="dash-grid">
        <StatCard
          icon={<UserOutlined />}
          label="用户总数"
          value={Number(overview.userCount ?? 0).toLocaleString()}
          delta={`今日新增 ${Number(overview.todayNewUsers ?? 0).toLocaleString()}`}
        />
        <StatCard
          icon={<PlaySquareOutlined />}
          label="番剧总数"
          value={Number(overview.subjectCount ?? 0).toLocaleString()}
          delta={`导入任务 ${Number(overview.importCount ?? 0).toLocaleString()}`}
          tone="blue"
        />
        <StatCard
          icon={<HeartOutlined />}
          label="收藏总数"
          value={Number(overview.collectionCount ?? 0).toLocaleString()}
          delta={`今日新增 ${Number(overview.todayNewCollections ?? 0).toLocaleString()}`}
          tone="amber"
        />
        <StatCard
          icon={<VideoCameraOutlined />}
          label="剧集总数"
          value={Number(overview.episodeCount ?? 0).toLocaleString()}
          tone="green"
        />
        <StatCard
          icon={<UserAddOutlined />}
          label="今日新增用户"
          value={Number(overview.todayNewUsers ?? 0).toLocaleString()}
          tone="amber"
        />
        <StatCard
          icon={<LoginOutlined />}
          label="今日登录"
          value={Number(overview.todayLogins ?? 0).toLocaleString()}
          tone="blue"
        />

        <section className="panel chart-lg">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">01</span>运营趋势
              </h3>
              <div className="panel-sub">每日新增用户 / 新增收藏 / 登录</div>
            </div>
            <span className="panel-note">近 {range} 天</span>
          </div>
          <TrendChart data={trends} />
        </section>

        <section className="panel chart-md">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">02</span>收藏类型
              </h3>
              <div className="panel-sub">用户收藏状态分布</div>
            </div>
          </div>
          <DonutChart
            items={collectionItems}
            centerLabel="总收藏"
            centerValue={collectionTotal.toLocaleString()}
          />
        </section>

        <section className="panel chart-third">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">03</span>评分分布
              </h3>
              <div className="panel-sub">1-10 分收藏评分</div>
            </div>
          </div>
          <div className="score-bars">
            {ratings.map((item) => (
              <div className="score-bar" key={item.rate} title={`${item.rate} 分：${item.count}`}>
                <div className="fill" style={{ height: `${(item.count / maxScore) * 100}%` }} />
                <span className="score">{item.rate}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="panel chart-third">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">04</span>季度数量
              </h3>
              <div className="panel-sub">按放送日期聚合条目数</div>
            </div>
          </div>
          <BarList items={seasonItems} />
        </section>

        <section className="panel chart-third">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">05</span>导入状态
              </h3>
              <div className="panel-sub">条目导入状态统计</div>
            </div>
          </div>
          <div className="import-metrics">
            <div className="import-metric running">
              <span>总数</span>
              <strong>{subjectStats.importStat?.importTotal ?? 0}</strong>
            </div>
            <div className="import-metric success">
              <span>成功</span>
              <strong>{subjectStats.importStat?.importSucceeded ?? 0}</strong>
            </div>
            <div className="import-metric failed">
              <span>失败</span>
              <strong>{subjectStats.importStat?.importFailed ?? 0}</strong>
            </div>
          </div>
          <BarList items={importStatusItems} />
        </section>

        <section className="panel chart-lg">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">06</span>热门榜
              </h3>
              <div className="panel-sub">本站收藏最多的前 5 名</div>
            </div>
          </div>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>条目</th>
                  <th>收藏数</th>
                  <th>占比</th>
                </tr>
              </thead>
              <tbody>
                {hotSubjects.map((item, index) => (
                  <tr key={item.id}>
                    <td>
                      <span className={`rank-no${index < 3 ? ' top' : ''}`}>
                        {String(index + 1).padStart(2, '0')}
                      </span>
                    </td>
                    <td>
                      <div className="rank-cell">
                        {item.image ? (
                          <img className="poster-thumb" src={item.image} alt={item.nameCn || item.name} />
                        ) : (
                          <span
                            className="poster-thumb"
                            style={{
                              background: `linear-gradient(135deg, hsl(${hueOf(item.id)} 42% 26%), hsl(${(hueOf(item.id) + 45) % 360} 52% 10%))`,
                            }}
                          >
                            {(item.nameCn || item.name).slice(0, 1)}
                          </span>
                        )}
                        <span className="subject-name">
                          <b>{item.nameCn || item.name}</b>
                          <span>{item.name}</span>
                        </span>
                      </div>
                    </td>
                    <td className="num">{Number(item.collectionCount ?? 0).toLocaleString()}</td>
                    <td>
                      <div className="bar-track" style={{ maxWidth: 180 }}>
                        <div
                          className="bar-fill"
                          style={{ width: `${(Number(item.collectionCount ?? 0) / maxHot) * 100}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="panel chart-md">
          <div className="panel-head">
            <div>
              <h3 className="panel-title">
                <span className="seq">07</span>最近导入
              </h3>
              <div className="panel-sub">
                {records.length} 条任务记录 · 最近 {importStatus.lastImportedAt ?? '-'}
              </div>
            </div>
            <span className="panel-note">
              <ThunderboltOutlined /> {Number(importStatus.totalSubjects ?? 0).toLocaleString()}
            </span>
          </div>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>季度</th>
                  <th>状态</th>
                  <th>条目</th>
                  <th>开始</th>
                </tr>
              </thead>
              <tbody>
                {records.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="empty-cell">
                      暂无导入记录
                    </td>
                  </tr>
                ) : (
                  records.slice(0, 4).map((record: ImportRecordVO) => (
                    <tr key={record.id}>
                      <td className="num">{record.season || '-'}</td>
                      <td>
                        <span className={`status-tag ${record.status.toLowerCase()}`}>
                          <span className={`status-dot${record.status === 'RUNNING' ? ' running' : ''}`} />
                          {statusLabel[record.status]}
                        </span>
                      </td>
                      <td className="num">{Number(record.subjectCount ?? 0).toLocaleString()}</td>
                      <td className="num">{record.startedAt ?? '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
