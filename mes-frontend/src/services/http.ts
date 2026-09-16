import { apiClient, toApiError } from "./axiosConfig";

/** Ném ra ApiError đã chuẩn hoá, để mọi hook bắt cùng một kiểu. */
async function request<T>(p: Promise<{ data: T }>): Promise<T> {
  try {
    return (await p).data;
  } catch (e) {
    throw toApiError(e);
  }
}

export const getData = <T>(url: string, params?: Record<string, unknown>) =>
  request<T>(apiClient.get<T>(url, { params }));

export const postData = <T, P = unknown>(url: string, payload?: P, cfg?: { headers?: Record<string, string> }) =>
  request<T>(apiClient.post<T>(url, payload, cfg));

export const deleteData = <T>(url: string) => request<T>(apiClient.delete<T>(url));
