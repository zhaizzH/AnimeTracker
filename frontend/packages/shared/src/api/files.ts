import { postForm } from './http';
export const upload = (file: File, type: 'avatar' | 'cover') => {
  const fd = new FormData();
  fd.append('file', file);
  return postForm<string>(`/common/files/upload?type=${type}`, fd);
};
