import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { chatService } from '../services/chatService';
import { ChatSession, ChatMessage, SendMessageResponse, MultiDayTripOptimizationResponse } from '../types';
import { ReplanningDiffView } from '../components/chat/ReplanningDiffView';
import { ChatMessageRenderer } from '../components/chat/ChatMessageRenderer';
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
  MapPin,
  Pencil,
  Check,
  X,
  Trash2,
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
  const [latestItinerary, setLatestItinerary] = useState<MultiDayTripOptimizationResponse | null>(null);

  // Renaming state
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  // Refs for smooth container-only scrolling and maintaining focus
  const chatScrollContainerRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLInputElement>(null);
  const editInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (currentSessionId) {
      loadSessionMessages(currentSessionId);
      setTimeout(() => chatInputRef.current?.focus(), 50);
    }
  }, [currentSessionId]);

  // Scroll ONLY the chat messages container, NEVER scrolling/shifting the outer window
  useEffect(() => {
    if (chatScrollContainerRef.current) {
      chatScrollContainerRef.current.scrollTo({
        top: chatScrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages, loading]);

  useEffect(() => {
    if (editingSessionId && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [editingSessionId]);

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
      setTimeout(() => chatInputRef.current?.focus(), 50);
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
      setTimeout(() => chatInputRef.current?.focus(), 50);
    }
  };

  const handleStartRename = (e: React.MouseEvent, session: ChatSession) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const handleSaveRename = async (e: React.MouseEvent | React.FormEvent, sessionId: string) => {
    e.stopPropagation();
    e.preventDefault();
    if (!editingTitle.trim()) return;

    try {
      const updated = await chatService.renameSession(sessionId, editingTitle.trim());
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: updated.title } : s))
      );
      setEditingSessionId(null);
    } catch (err) {
      console.error('Failed to rename session', err);
    }
  };

  const handleCancelRename = (e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(null);
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this planning session?')) return;

    try {
      await chatService.deleteSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (currentSessionId === sessionId) {
        if (remaining.length > 0) {
          setCurrentSessionId(remaining[0].id);
        } else {
          createNewSession();
        }
      }
    } catch (err) {
      console.error('Failed to delete session', err);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !currentSessionId || loading) return;

    const userText = input.trim();
    setInput('');
    // Keep focus active in input box
    chatInputRef.current?.focus();

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

      if (response.itinerary) {
        setLatestItinerary(response.itinerary);
        // Refresh sessions to get any auto-updated title
        const refreshedList = await chatService.getSessions();
        setSessions(refreshedList);
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
      // Ensure cursor stays focused in input field without needing manual click
      setTimeout(() => chatInputRef.current?.focus(), 50);
    }
  };

  const handleOpenItinerary = () => {
    if (latestItinerary) {
      navigate(`/itinerary/${latestItinerary.trip_id || ''}`, {
        state: {
          generatedData: {
            trip_id: latestItinerary.trip_id,
            itinerary_id: latestItinerary.trip_id,
            title: `${latestItinerary.destination_id.toUpperCase()} Itinerary`,
            destination_id: latestItinerary.destination_id,
            itinerary: latestItinerary,
          },
        },
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-xl mx-auto py-16 text-center space-y-4">
        <div className="inline-flex p-3 bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 rounded-2xl border border-emerald-100 dark:border-emerald-800/60">
          <Sparkles className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Conversational AI Travel Assistant</h2>
        <p className="text-sm text-slate-500 dark:text-neutral-400">
          Please sign in to start a conversational trip planning session and enable smart replanning.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] h-[calc(100vh-64px)] max-w-7xl mx-auto p-3 sm:p-5 flex flex-col justify-between">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 h-full flex-1 overflow-hidden">
        {/* Left Sidebar: Sessions List (4 cols) */}
        <div className="liquid-glass md:col-span-4 rounded-3xl p-5 border border-slate-200 dark:border-neutral-800 shadow-sm flex flex-col justify-between overflow-hidden h-full">
        <div className="space-y-4 flex-1 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-900 dark:text-white text-sm flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <span>Planning Sessions</span>
            </h3>
            <button
              onClick={createNewSession}
              className="liquid-btn p-1.5 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/70 rounded-xl cursor-pointer flex items-center gap-1 text-xs font-bold px-2.5 border border-emerald-200/60 dark:border-emerald-800/60"
              title="New Session"
            >
              <Plus className="w-4 h-4" />
              <span>New</span>
            </button>
          </div>

          <div className="space-y-2 overflow-y-auto flex-1 pr-1">
            {sessions.map((s) => {
              const isActive = currentSessionId === s.id;
              const isEditing = editingSessionId === s.id;

              return (
                <div
                  key={s.id}
                  onClick={() => !isEditing && setCurrentSessionId(s.id)}
                  className={`liquid-card-interactive group relative p-3.5 rounded-2xl cursor-pointer text-xs border transition-all ${
                    isActive
                      ? 'bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black font-extrabold shadow-md border-emerald-600 dark:border-emerald-400'
                      : 'bg-slate-50 dark:bg-neutral-900/70 text-slate-700 dark:text-neutral-200 hover:bg-slate-100 dark:hover:bg-neutral-800 border-slate-100 dark:border-neutral-800/80 hover:border-emerald-300 dark:hover:border-emerald-500/50'
                  }`}
                >
                  {isEditing ? (
                    <form
                      onSubmit={(e) => handleSaveRename(e, s.id)}
                      className="flex items-center gap-1.5"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <input
                        ref={editInputRef}
                        type="text"
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        className={`flex-1 px-2.5 py-1 text-xs rounded-lg border outline-none font-bold ${
                          isActive
                            ? 'bg-white text-slate-900 border-emerald-300'
                            : 'bg-white dark:bg-black text-slate-900 dark:text-white border-slate-300 dark:border-neutral-700'
                        }`}
                        onKeyDown={(e) => {
                          if (e.key === 'Escape') setEditingSessionId(null);
                        }}
                      />
                      <button
                        type="submit"
                        title="Save name"
                        className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                          isActive
                            ? 'bg-emerald-800 dark:bg-black hover:bg-emerald-900 text-white dark:text-emerald-400'
                            : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                        }`}
                      >
                        <Check className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={handleCancelRename}
                        title="Cancel"
                        className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                          isActive
                            ? 'bg-emerald-800 dark:bg-neutral-800 text-emerald-200 dark:text-neutral-300'
                            : 'bg-slate-200 dark:bg-neutral-800 hover:bg-slate-300 dark:hover:bg-neutral-700 text-slate-600 dark:text-neutral-300'
                        }`}
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </form>
                  ) : (
                    <div className="flex items-center justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="truncate font-bold mb-0.5">{s.title}</p>
                        <p
                          className={`text-[10px] ${
                            isActive ? 'text-emerald-100 dark:text-black/80 font-medium' : 'text-slate-400 dark:text-neutral-500'
                          }`}
                        >
                          {s.created_at
                            ? new Date(s.created_at).toLocaleDateString()
                            : 'Active session'}
                        </p>
                      </div>

                      {/* Action buttons (Rename & Delete) */}
                      <div
                        className={`flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ${
                          isActive ? 'opacity-100' : ''
                        }`}
                      >
                        <button
                          type="button"
                          onClick={(e) => handleStartRename(e, s)}
                          title="Rename trip session"
                          className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                            isActive
                              ? 'bg-emerald-700 dark:bg-neutral-900 hover:bg-emerald-800 dark:hover:bg-black text-white dark:text-emerald-400'
                              : 'bg-slate-200 dark:bg-neutral-800 hover:bg-slate-300 dark:hover:bg-neutral-700 text-slate-700 dark:text-neutral-300'
                          }`}
                        >
                          <Pencil className="w-3 h-3" />
                        </button>

                        <button
                          type="button"
                          onClick={(e) => handleDeleteSession(e, s.id)}
                          title="Delete trip session"
                          className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                            isActive
                              ? 'bg-emerald-700 dark:bg-neutral-900 hover:bg-rose-600 text-emerald-100 dark:text-neutral-400 hover:text-white'
                              : 'bg-slate-200 dark:bg-neutral-800 hover:bg-rose-100 dark:hover:bg-rose-950/60 text-slate-500 dark:text-neutral-400 hover:text-rose-600 dark:hover:text-rose-400'
                          }`}
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 dark:border-neutral-800/80 space-y-2">
          {latestItinerary && (
            <button
              onClick={handleOpenItinerary}
              className="liquid-btn w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-md cursor-pointer"
            >
              <MapPin className="w-4 h-4" />
              <span>View Map & Itinerary ({latestItinerary.total_days} Days)</span>
            </button>
          )}

          <button
            onClick={() => navigate('/plan')}
            className="liquid-btn w-full py-2.5 px-4 bg-slate-100 dark:bg-neutral-900 hover:bg-slate-200 dark:hover:bg-neutral-800 text-slate-700 dark:text-neutral-200 rounded-xl font-bold text-xs flex items-center justify-center gap-2 border border-transparent dark:border-neutral-800 cursor-pointer"
          >
            <Compass className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
            <span>Open Wizard Planner</span>
          </button>
        </div>
      </div>

      {/* Right Column: Chat Stream & Input (8 cols) */}
      <div className="liquid-glass md:col-span-8 rounded-3xl border border-slate-200 dark:border-neutral-800 shadow-sm flex flex-col overflow-hidden h-full">
        {/* Chat Stream (Only this inner container scrolls smoothly to bottom) */}
        <div ref={chatScrollContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/40 dark:bg-black/60">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex items-start gap-3 ${
                m.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs shrink-0 mt-0.5 ${
                  m.sender === 'user' ? 'bg-emerald-600 text-white' : 'bg-slate-200 dark:bg-neutral-800 text-slate-700 dark:text-neutral-300'
                }`}
              >
                {m.sender === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />}
              </div>

              <div
                className={`max-w-[88%] p-4 rounded-2xl text-xs md:text-sm leading-relaxed ${
                  m.sender === 'user'
                    ? 'liquid-btn bg-emerald-600 dark:bg-emerald-600 text-white rounded-tr-none shadow-sm font-medium'
                    : 'liquid-card bg-white dark:bg-neutral-900/90 text-slate-800 dark:text-neutral-100 rounded-tl-none border border-slate-200 dark:border-neutral-800 shadow-sm'
                }`}
              >
                <ChatMessageRenderer
                  content={m.content}
                  isUser={m.sender === 'user'}
                  onSuggestionClick={(suggestion) => {
                    setInput(suggestion);
                    setTimeout(() => chatInputRef.current?.focus(), 20);
                  }}
                />
              </div>
            </div>
          ))}

          {latestDiff && <ReplanningDiffView diff={latestDiff} />}

          {latestItinerary && (
            <div className="liquid-card p-4 bg-emerald-50/80 dark:bg-neutral-950 border border-emerald-200 dark:border-emerald-500/30 rounded-2xl flex flex-wrap items-center justify-between gap-3 shadow-sm">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-600 dark:bg-emerald-500 text-white dark:text-black flex items-center justify-center font-bold text-xs">
                  <MapPin className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-emerald-950 dark:text-emerald-300 uppercase tracking-wider">
                    {latestItinerary.destination_id} &bull; {latestItinerary.total_days} Days ({latestItinerary.total_scheduled_attractions} Stops)
                  </h4>
                  <p className="text-[11px] text-emerald-700 dark:text-emerald-400">
                    Road Travel: {latestItinerary.total_travel_distance_km} km &bull; Est. Cost: ₹{Math.round(latestItinerary.total_estimated_cost).toLocaleString()}
                  </p>
                </div>
              </div>

              <button
                onClick={handleOpenItinerary}
                className="liquid-btn px-4 py-2 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-bold rounded-xl text-xs flex items-center gap-1.5 shadow-sm cursor-pointer"
              >
                <span>View Full Map & Timeline</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {loading && (
            <div className="liquid-card flex items-center gap-2 text-slate-500 dark:text-neutral-400 text-xs bg-white dark:bg-neutral-900 p-3 rounded-xl border border-slate-200 dark:border-neutral-800 w-fit">
              <Loader2 className="w-4 h-4 animate-spin text-emerald-600 dark:text-emerald-400" />
              <span>Analyzing constraints & optimizing itinerary...</span>
            </div>
          )}
        </div>

        {/* Input Bar (Keeps cursor focus retained at all times) */}
        <form
          onSubmit={handleSend}
          className="p-4 bg-white dark:bg-black border-t border-slate-200 dark:border-neutral-800 flex items-center gap-3"
        >
          <input
            ref={chatInputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your travel request (e.g. 'Plan 3 days in Goa with auto') or reply '3' or 'make it 2 days'..."
            className="flex-1 px-4 py-3 bg-slate-50 dark:bg-neutral-950 border border-slate-200 dark:border-neutral-800 rounded-xl text-xs md:text-sm text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white dark:focus:bg-black transition-all"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="liquid-btn p-3 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-bold rounded-xl shadow-md disabled:opacity-50 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  </div>
  );
};
