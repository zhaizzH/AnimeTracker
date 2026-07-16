import http from './http'
import type { ApiResponse } from '@/types'

/**
 * 上传文件到 MinIO
 * @param file 图片文件 (jpg/png/webp)
 * @param type 上传分类: avatar | cover
 * @returns MinIO 可访问 URL
 */
export async function uploadFile(file: File, type: 'avatar' | 'cover' = 'avatar'): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)

  const res = await http.post<ApiResponse<string>>('/api/common/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return res.data.data
}
