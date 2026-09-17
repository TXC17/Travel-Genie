import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { chatService } from '../../services/chatService';
import { ChatMessage, SendMessageResponse, MultiDayTripOptimizationResponse } from '../../types';
import { ReplanningDiffView } from './ReplanningDiffView';
import {
  MessageSquare,
  Send,
  Loader2,
  Sparkles,
  Bot,
  User as UserIcon,
  X,
  Minimize2,
  Maximize2,
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isAuthenticated && !sessionId) {
      initSession();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 bg-teal-600 hover:bg-teal-700 text-white p-4 rounded-full shadow-2xl flex items-center gap-2.5 transition-all hover:scale-105 cursor-pointer"
      >
        <Sparkles className="w-5 h-5 animate-pulse" />
        <span className="font-bold text-sm pr-1">AI Assistant</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-40 w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col h-[560px] animate-in slide-in-from-bottom-5 duration-200">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-700 to-teal-800 text-white p-4 flex items-center justify-between shadow-md">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-teal-500/30 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-teal-200" />
          </div>
          <div>
            <h3 className="font-bold text-sm">Travel Genie AI Planner</h3>
            <p className="text-[10px] text-teal-200">Natural-Language Planning & Replanning</p>
          </div>
        </div>

        <button
          onClick={() => setIsOpen(false)}
          className="text-teal-200 hover:text-white transition-colors p-1"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Message Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/50">
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
                  ? 'bg-teal-600 text-white'
                  : 'bg-slate-200 text-slate-700'
              }`}
            >
              {m.sender === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            <div
              className={`max-w-[85%] p-3.5 rounded-2xl text-xs leading-relaxed ${
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

      {/* Input Box */}
      <form onSubmit={handleSend} className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isAuthenticated ? "Type a prompt or replanning change..." : "Please log in to chat..."}
          disabled={!isAuthenticated || loading}
          className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:bg-white transition-all disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={!isAuthenticated || loading || !input.trim()}
          className="p-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-md disabled:opacity-50 transition-all cursor-pointer"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
