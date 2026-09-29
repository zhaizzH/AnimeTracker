import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { adminDashboardApi } from '@shared';
import { AudienceMix } from '@/components/dashboard/audience-mix';
import { BrowserShare } from '@/components/dashboard/browser-share';
import { OnlineNow } from '@/components/dashboard/online-now';
import { TopCountries } from '@/components/dashboard/top-countries';
import { TopPages } from '@/components/dashboard/top-pages';
import { TopReferrers } from '@/components/dashboard/top-referrers';
import { TrafficSourcesChart } from '@/components/dashboard/traffic-sources-chart';
import { VisitorsChart } from '@/components/dashboard/visitors-chart';
import { WebVitals } from '@/components/dashboard/web-vitals';
import { toCompositeCardState } from '@/components/dashboard/card-state';

export default function Dashboard() {
  const [days, setDays] = useState(30);
  const ov = useQuery({ queryKey: ['dash', 'overview'], queryFn: adminDashboardApi.overview });
  const tr = useQuery({
    queryKey: ['dash', 'trends', days],
    queryFn: () => adminDashboardApi.trends(days),
  });
  const cs = useQuery({ queryKey: ['dash', 'cs'], queryFn: adminDashboardApi.collectionStats });
  const ss = useQuery({ queryKey: ['dash', 'ss'], queryFn: adminDashboardApi.subjectStats });
  const ht = useQuery({ queryKey: ['dash', 'hot'], queryFn: () => adminDashboardApi.hot(10) });

  // 导入卡片同时依赖 overview 与 subjectStats：任一失败即失败，任一加载即加载。
  const importState = toCompositeCardState(
    [
      { isLoading: ov.isLoading, isError: ov.isError },
      { isLoading: ss.isLoading, isError: ss.isError },
    ],
    false,
  );

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      <VisitorsChart
        days={days}
        isError={tr.isError}
        isLoading={tr.isLoading}
        onDaysChange={setDays}
        points={tr.data}
      />
      <OnlineNow
        isError={ov.isError}
        isLoading={ov.isLoading}
        todayLogins={ov.data?.todayLogins}
        todayNewCollections={ov.data?.todayNewCollections}
        todayNewUsers={ov.data?.todayNewUsers}
      />
      <TopPages isError={ht.isError} isLoading={ht.isLoading} items={ht.data} />
      <TopCountries
        isError={ss.isError}
        isLoading={ss.isLoading}
        seasons={ss.data?.seasons}
      />
      <TrafficSourcesChart
        isError={cs.isError}
        isLoading={cs.isLoading}
        types={cs.data?.types}
      />
      <AudienceMix
        isError={cs.isError}
        isLoading={cs.isLoading}
        ratings={cs.data?.ratings}
      />
      <BrowserShare
        isError={ss.isError}
        isLoading={ss.isLoading}
        scoreCounts={ss.data?.scoreCounts}
      />
      <TopReferrers
        importStatuses={ss.data?.importStatuses}
        isError={ss.isError}
        isLoading={ss.isLoading}
      />
      <WebVitals
        importCount={ov.data?.importCount}
        importFailed={ss.data?.importStat.importFailed}
        importSucceeded={ss.data?.importStat.importSucceeded}
        state={importState}
      />
    </div>
  );
}
