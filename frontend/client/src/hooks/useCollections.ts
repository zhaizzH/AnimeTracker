import { useMutation, useQueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { collectionsApi } from '@/api/collections';
import type { CollectionUpdateDTO } from '@/types';

export function useCollections() {
  const queryClient = useQueryClient();

  const saveMutation = useMutation({
    mutationFn: ({ subjectId, data }: { subjectId: number; data: CollectionUpdateDTO }) =>
      collectionsApi.save(subjectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      message.success('更新成功');
    },
    onError: (err: any) => message.error(err.message || '操作失败'),
  });

  const removeMutation = useMutation({
    mutationFn: (subjectId: number) => collectionsApi.remove(subjectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      message.success('已取消收藏');
    },
    onError: (err: any) => message.error(err.message || '操作失败'),
  });

  const epStatusMutation = useMutation({
    mutationFn: ({ subjectId, epStatus }: { subjectId: number; epStatus: number }) =>
      collectionsApi.updateEpStatus(subjectId, { epStatus }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    },
  });

  return { saveMutation, removeMutation, epStatusMutation };
}
