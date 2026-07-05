import React, { useState, useRef, useEffect } from 'react';
import { Send, X, Sparkles, Trash2, User } from 'lucide-react';
import { api } from '../App';

const AIAssistant = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (open && suggestions.length === 0) {
      api.get('/ai/suggestions')
        .then(r => setSuggestions(r.data.suggestions || []))
        .catch(() => setSuggestions([]));
    }
  }, [open, suggestions.length]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  const sendMessage = async (text) => {
    const msg = (text || input || '').trim();
    if (!msg || loading) return;
    setInput('');
    const newHistory = messages.concat([{ role: 'user', content: msg }]);
    setMessages(newHistory);
    setLoading(true);
    try {
      const response = await api.post('/ai/chat', {
        message: msg,
        history: messages.slice(-10),
      });
      setMessages(newHistory.concat([{ role: 'assistant', content: response.data.reply }]));
    } catch (e) {
      const errMsg = (e && e.response && e.response.data && e.response.data.detail) || 'Dicka shkoi keq.';
      setMessages(newHistory.concat([{ role: 'assistant', content: 'Gabim: ' + errMsg }]));
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    try { await api.delete('/ai/history'); } catch (e) {}
    setMessages([]);
  };

  const bubbleUser = 'bg-[#2563EB] text-white rounded-br-md';
  const bubbleAi = 'bg-white border border-gray-200 text-gray-800 rounded-bl-md';

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-gradient-to-br from-[#2563EB] to-[#1E3A8A] hover:scale-105 text-white rounded-full shadow-xl flex items-center justify-center transition-all"
          title="Datapos AI Asistent"
        >
          <Sparkles className="h-6 w-6" strokeWidth={2} />
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-emerald-500 rounded-full ring-2 ring-white animate-pulse" />
        </button>
      )}

      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-[400px] max-w-[calc(100vw-2rem)] h-[600px] max-h-[calc(100vh-3rem)] bg-white rounded-3xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden">
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-[#2563EB] to-[#1E3A8A] text-white flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
                <Sparkles className="h-4 w-4" strokeWidth={2.5} />
              </div>
              <div>
                <p className="font-semibold text-sm leading-tight">Datapos AI</p>
                <p className="text-[11px] text-blue-100">Asistenti yt inteligjent</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={clearHistory} className="w-8 h-8 hover:bg-white/10 rounded-lg flex items-center justify-center transition-colors" title="Pastro historine">
                <Trash2 className="h-4 w-4" />
              </button>
              <button onClick={() => setOpen(false)} className="w-8 h-8 hover:bg-white/10 rounded-lg flex items-center justify-center transition-colors">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {messages.length === 0 && (
              <div className="text-center py-4">
                <div className="w-14 h-14 bg-gradient-to-br from-[#2563EB] to-[#1E3A8A] rounded-2xl mx-auto flex items-center justify-center mb-3 shadow-lg">
                  <Sparkles className="h-6 w-6 text-white" strokeWidth={2} />
                </div>
                <p className="font-semibold text-gray-900">Si mund te te ndihmoj?</p>
                <p className="text-xs text-gray-500 mt-1">Pyet per shitjet, stokun, klientet...</p>
                {suggestions.length > 0 && (
                  <div className="mt-5 space-y-2">
                    {suggestions.map((s, i) => (
                      <button
                        key={i}
                        onClick={() => sendMessage(s)}
                        className="w-full text-left text-sm px-3 py-2.5 bg-white border border-gray-200 hover:border-[#2563EB] hover:bg-blue-50 rounded-xl transition-all"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={'flex gap-2 ' + (m.role === 'user' ? 'justify-end' : 'justify-start')}>
                {m.role === 'assistant' && (
                  <div className="w-8 h-8 bg-gradient-to-br from-[#2563EB] to-[#1E3A8A] rounded-full flex-shrink-0 flex items-center justify-center">
                    <Sparkles className="h-4 w-4 text-white" strokeWidth={2.5} />
                  </div>
                )}
                <div className={'max-w-[80%] px-3.5 py-2.5 rounded-2xl text-sm ' + (m.role === 'user' ? bubbleUser : bubbleAi)}>
                  <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
                </div>
                {m.role === 'user' && (
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex-shrink-0 flex items-center justify-center">
                    <User className="h-4 w-4 text-gray-700" strokeWidth={2} />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-2 justify-start">
                <div className="w-8 h-8 bg-gradient-to-br from-[#2563EB] to-[#1E3A8A] rounded-full flex-shrink-0 flex items-center justify-center">
                  <Sparkles className="h-4 w-4 text-white" strokeWidth={2.5} />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.15s]" />
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.3s]" />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-3 bg-white border-t border-gray-200 flex-shrink-0">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); sendMessage(); } }}
                placeholder="Shkruaj pyetjen..."
                disabled={loading}
                className="flex-1 px-4 h-11 bg-gray-100 rounded-xl text-sm border-0 focus:ring-2 focus:ring-[#2563EB] focus:bg-white outline-none transition-all disabled:opacity-50"
              />
              <button
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                className="w-11 h-11 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:bg-gray-300 text-white rounded-xl flex items-center justify-center transition-colors flex-shrink-0"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <p className="text-[10px] text-gray-400 mt-1.5 text-center">Datapos AI - Powered by Gemini 2.0</p>
          </div>
        </div>
      )}
    </>
  );
};

export default AIAssistant;