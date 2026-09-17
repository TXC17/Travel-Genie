import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { chatService } from '../services/chatService';
import { ChatSession, ChatMessage, SendMessageResponse } from '../types';
import { ReplanningDiffView } from '../components/chat/ReplanningDiffView';
import {
  Sparkles,
  Send,
  Loader2,
  Bot,
  User as UserIcon,
  Plus,
  Compass,
  ArrowRight,
  MessageSquare,
} from 'lucide-react';

export const ChatPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [latestDiff, setLatestDiff] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (currentSessionId) {
      loadSessionMessages(currentSessionId);
    }
  }, [currentSessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadSessions = async () => {
    try {
      const list = await chatService.getSessions();
      setSessions(list);
      if (list.length > 0 && !currentSessionId) {
        setCurrentSessionId(list[0].id);
      } else if (list.length === 0) {
        createNewSession();
      }
    } catch (err) {
      console.error('Failed to load chat sessions', err);
    }
  };

  const createNewSession = async () => {
    try {
      const session = await chatService.createSession('New Travel Plan');
      setSessions((prev) => [session, ...prev]);
      setCurrentSessionId(session.id);
      setMessages([
        {
          id: 'welcome',
          session_id: session.id,
          sender: 'assistant',
          content:
            '👋 Hello! I am your AI Travel Genie assistant. Ask me to plan a trip to Hampi, Coorg, Dandeli, or Goa! (e.g. *"Plan a 3-day Hampi trip for 2 people with a ₹15,000 budget and auto transport"*).',
        },
      ]);
    } catch (err) {
      console.error('Failed to create new session', err);
    }
  };

  const loadSessionMessages = async (id: string) => {
    try {
      setLoading(true);
      const session = await chatService.getSession(id);
      if (session.messages && session.messages.length > 0) {
        setMessages(session.messages);
      } else {
        setMessages([
          {
            id: 'welcome',
            session_id: id,
            sender: 'assistant',
            content:
              '👋 Tell me what kind of trip you would like to plan! You can also request replanning changes anytime.',
          },
        ]);
      }
    } catch (err) {
      console.error('Failed to load session detail', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !currentSessionId || loading) return;

    const userText = input.trim();
    setInput('');

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      session_id: currentSessionId,
      sender: 'user',
      content: userText,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response: SendMessageResponse = await chatService.sendMessage(
        currentSessionId,
        userText
      );

      const assistantMsg: ChatMessage = {
        id: response.message_id,
        session_id: response.session_id,
        sender: 'assistant',
        content: response.content,
        extracted_constraints: response.extracted_constraints as any,
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (response.replanning_diff) {
        setLatestDiff(response.replanning_diff);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        session_id: currentSessionId,
        sender: 'assistant',
        content: '⚠️ Failed to process planning request. Please try again.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <div className="inline-flex p-3 bg-teal-50 text-teal-600 rounded-2xl">
          <Sparkles className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Conversational AI Travel Assistant</h2>
        <p className="text-sm text-slate-500">
          Please sign in to start a conversational trip planning session and enable smart replanning.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-6 grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-140px)] min-h-[580px]">
      {/* Left Sidebar: Sessions List (4 cols) */}
      <div className="md:col-span-4 bg-white rounded-3xl p-5 border border-slate-200 shadow-sm flex flex-col justify-between overflow-hidden">
        <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-teal-600" />
              <span>Planning Sessions</span>
            </h3>
            <button
              onClick={createNewSession}
              className="p-1.5 bg-teal-50 text-teal-700 hover:bg-teal-100 rounded-xl transition-all cursor-pointer"
              title="New Session"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-2 overflow-y-auto flex-1 pr-1">
            {sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => setCurrentSessionId(s.id)}
                className={`p-3.5 rounded-2xl cursor-pointer transition-all text-xs ${
                  currentSessionId === s.id
                    ? 'bg-teal-600 text-white font-semibold shadow-md'
                    : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                }`}
              >
                <p className="truncate font-bold mb-0.5">{s.title}</p>
                <p className={`text-[10px] ${currentSessionId === s.id ? 'text-teal-100' : 'text-slate-400'}`}>
                  {s.created_at ? new Date(s.created_at).toLocaleDateString() : 'Active session'}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100">
          <button
            onClick={() => navigate('/plan')}
            className="w-full py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            <Compass className="w-4 h-4" />
            <span>Open Wizard Planner</span>
          </button>
        </div>
      </div>

      {/* Right Column: Chat Stream & Input (8 cols) */}
      <div className="md:col-span-8 bg-white rounded-3xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        {/* Chat Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/40">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex items-start gap-3 ${
                m.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs shrink-0 mt-0.5 ${
                  m.sender === 'user' ? 'bg-teal-600 text-white' : 'bg-slate-200 text-slate-700'
                }`}
              >
                {m.sender === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-[80%] p-4 rounded-2xl text-xs md:text-sm leading-relaxed ${
                  m.sender === 'user'
                    ? 'bg-teal-600 text-white rounded-tr-none shadow-sm'
                    : 'bg-white text-slate-800 rounded-tl-none border border-slate-200 shadow-sm whitespace-pre-line'
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}

          {latestDiff && <ReplanningDiffView diff={latestDiff} />}

          {loading && (
            <div className="flex items-center gap-2 text-slate-500 text-xs bg-white p-3 rounded-xl border border-slate-200 w-fit">
              <Loader2 className="w-4 h-4 animate-spin text-teal-600" />
              <span>Analyzing constraints & optimizing itinerary...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={handleSend}
          className="p-4 bg-white border-t border-slate-200 flex items-center gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your travel request (e.g. 'Plan 3 days in Hampi with auto') or a replanning change..."
            disabled={loading}
            className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-xs md:text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-3 bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-md disabled:opacity-50 transition-all cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
