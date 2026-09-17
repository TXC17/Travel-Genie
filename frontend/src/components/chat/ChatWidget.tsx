import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { chatService } from '../../services/chatService';
import { ChatMessage, SendMessageResponse, MultiDayTripOptimizationResponse } from '../../types';
import { ReplanningDiffView } from './ReplanningDiffView';
import { ChatMessageRenderer } from './ChatMessageRenderer';
import {
  Send,
  Loader2,
  Sparkles,
  Bot,
  User as UserIcon,
  X,
} from 'lucide-react';

interface ChatWidgetProps {
  onItineraryUpdated?: (itinerary: MultiDayTripOptimizationResponse) => void;
  isOpenDefault?: boolean;
}

export const ChatWidget: React.FC<ChatWidgetProps> = ({
  onItineraryUpdated,
  isOpenDefault = false,
}) => {
  const { isAuthenticated } = useAuth();
  const [isOpen, setIsOpen] = useState(isOpenDefault);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [latestDiff, setLatestDiff] = useState<any>(null);

  const chatScrollContainerRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isAuthenticated && !sessionId) {
      initSession();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => chatInputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    if (chatScrollContainerRef.current) {
      chatScrollContainerRef.current.scrollTo({
        top: chatScrollContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages, loading]);

  const initSession = async () => {
    try {
      const session = await chatService.createSession('AI Travel Assistant');
      setSessionId(session.id);
      setMessages([
        {
          id: 'welcome',
          session_id: session.id,
          sender: 'assistant',
          content:
            '👋 Hi! I am your AI Travel Genie assistant. Tell me where you want to travel, for how many days, and your budget! (e.g. *"Plan a 3-day Hampi trip for 2 people with a ₹15,000 budget"*).',
        },
      ]);
    } catch (err) {
      console.error('Failed to initialize chat session', err);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId || loading) return;

    const userText = input.trim();
    setInput('');
    chatInputRef.current?.focus();

    // Append user message
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      session_id: sessionId,
      sender: 'user',
      content: userText,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response: SendMessageResponse = await chatService.sendMessage(sessionId, userText);

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

      if (response.itinerary && onItineraryUpdated) {
        onItineraryUpdated(response.itinerary);
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        session_id: sessionId,
        sender: 'assistant',
        content: '⚠️ Sorry, I encountered an issue processing your request. Please try again.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      setTimeout(() => chatInputRef.current?.focus(), 50);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-extrabold p-4 rounded-full shadow-2xl flex items-center gap-2.5 transition-all hover:scale-105 cursor-pointer shadow-emerald-500/20"
      >
        <Sparkles className="w-5 h-5 animate-pulse" />
        <span className="font-bold text-sm pr-1">AI Assistant</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-40 w-full max-w-md bg-white dark:bg-neutral-950 rounded-2xl shadow-2xl border border-slate-200 dark:border-neutral-800 overflow-hidden flex flex-col h-[560px] animate-in slide-in-from-bottom-5 duration-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-800 to-slate-900 dark:from-neutral-900 dark:to-black text-white p-4 flex items-center justify-between border-b border-emerald-700/40 dark:border-neutral-800 shadow-md">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white">Travel Genie AI Planner</h3>
            <p className="text-[10px] text-emerald-300">Natural-Language Planning & Replanning</p>
          </div>
        </div>

        <button
          onClick={() => setIsOpen(false)}
          className="text-neutral-400 hover:text-white transition-colors p-1 cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Message Stream */}
      <div ref={chatScrollContainerRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/50 dark:bg-black/80">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex items-start gap-2.5 ${
              m.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs shrink-0 mt-0.5 ${
                m.sender === 'user'
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-200 dark:bg-neutral-800 text-slate-700 dark:text-neutral-300'
              }`}
            >
              {m.sender === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4 text-emerald-400" />}
            </div>

            <div
              className={`max-w-[88%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                m.sender === 'user'
                  ? 'bg-emerald-600 text-white rounded-tr-none shadow-sm font-medium'
                  : 'bg-white dark:bg-neutral-900/90 text-slate-800 dark:text-neutral-100 rounded-tl-none border border-slate-200 dark:border-neutral-800 shadow-sm'
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

        {loading && (
          <div className="flex items-center gap-2 text-slate-500 dark:text-neutral-400 text-xs bg-white dark:bg-neutral-900 p-3 rounded-xl border border-slate-200 dark:border-neutral-800 w-fit">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-600 dark:text-emerald-400" />
            <span>Analyzing constraints & optimizing itinerary...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} className="p-3 bg-white dark:bg-black border-t border-slate-200 dark:border-neutral-800 flex items-center gap-2">
        <input
          ref={chatInputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isAuthenticated ? "Type a prompt or replanning change..." : "Please log in to chat..."}
          disabled={!isAuthenticated}
          className="flex-1 px-4 py-2.5 bg-slate-50 dark:bg-neutral-950 border border-slate-200 dark:border-neutral-800 rounded-xl text-xs text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white dark:focus:bg-black transition-all disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={!isAuthenticated || loading || !input.trim()}
          className="p-2.5 bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-400 text-white dark:text-black font-bold rounded-xl shadow-md disabled:opacity-50 transition-all cursor-pointer"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
