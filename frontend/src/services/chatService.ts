import { apiClient } from './api';
import { ChatSession, SendMessageResponse } from '../types';

export const chatService = {
  async createSession(title?: string, tripId?: string): Promise<ChatSession> {
    const res = await apiClient.post<ChatSession>('/chat/sessions', {
      title: title || 'New Travel Plan',
      trip_id: tripId,
    });
    return res.data;
  },

  async getSessions(): Promise<ChatSession[]> {
    const res = await apiClient.get<ChatSession[]>('/chat/sessions');
    return res.data;
  },

  async getSession(id: string): Promise<ChatSession> {
    const res = await apiClient.get<ChatSession>(`/chat/sessions/${id}`);
    return res.data;
  },

  async renameSession(id: string, title: string): Promise<ChatSession> {
    const res = await apiClient.patch<ChatSession>(`/chat/sessions/${id}`, {
      title: title.trim(),
    });
    return res.data;
  },

  async deleteSession(id: string): Promise<void> {
    await apiClient.delete(`/chat/sessions/${id}`);
  },

  async sendMessage(sessionId: string, content: string): Promise<SendMessageResponse> {
    const res = await apiClient.post<SendMessageResponse>(`/chat/sessions/${sessionId}/messages`, {
      content,
    });
    return res.data;
  },
};
