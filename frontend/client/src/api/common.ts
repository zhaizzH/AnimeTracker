import http from './client';

export const commonApi = {
  upload: (file: File, type: string = 'avatar') => {
    const formData = new FormData();
    formData.append('file', file);
    return http.post<string>('/common/files/upload', formData, {
      params: { type },
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
