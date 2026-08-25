import { postForm } from './http';

const uploadImage = (url: string, file: File) => {
  const form = new FormData();
  form.append('file', file);
  return postForm<string>(url, form);
};

export const uploadAvatar = (file: File) => uploadImage('/client/files/avatar', file);
export const uploadCover = (file: File) => uploadImage('/admin/files/cover', file);
