import { beforeEach, describe, expect, it, vi } from 'vitest';
import { postForm } from './http';
import { uploadAvatar, uploadCover } from './files';

vi.mock('./http', () => ({ postForm: vi.fn() }));

const mockedPostForm = vi.mocked(postForm);

describe('files api', () => {
  beforeEach(() => {
    mockedPostForm.mockReset();
    mockedPostForm.mockResolvedValue('http://minio/image.png' as never);
  });

  it('uploads avatar to the client-owned route', async () => {
    const file = new File(['avatar'], 'avatar.png', { type: 'image/png' });

    await uploadAvatar(file);

    expect(mockedPostForm).toHaveBeenCalledWith('/client/files/avatar', expect.any(FormData));
    expect((mockedPostForm.mock.calls[0][1] as FormData).get('file')).toBe(file);
  });

  it('uploads cover to the admin-owned route', async () => {
    const file = new File(['cover'], 'cover.webp', { type: 'image/webp' });

    await uploadCover(file);

    expect(mockedPostForm).toHaveBeenCalledWith('/admin/files/cover', expect.any(FormData));
    expect((mockedPostForm.mock.calls[0][1] as FormData).get('file')).toBe(file);
  });
});
