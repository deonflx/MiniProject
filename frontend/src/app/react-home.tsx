'use client';
import ReactMarkdown from 'react-markdown';
import { useState, useEffect, useRef } from 'react';
import LoginSignup from '../components/react-login-signup';
import { apiFetch, API_BASE } from '../api';
import { LogOut, User as UserIcon, ImagePlus, Loader2 } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function Home() {
  const [user, setUser] = useState<any>(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [sessionId, setSessionId] = useState('');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [stage, setStage] = useState<'sales' | 'kyc' | 'credit' | 'loan_selection' | 'docs' | 'done'>('sales');
  const [pdfPath, setPdfPath] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    checkAuth();
    setSessionId(`session_${Math.random().toString(36).substring(7)}`);
  }, []);

  const checkAuth = async () => {
    try {
      const res = await apiFetch('/api/auth/me/');
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setAuthChecking(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiFetch('/api/auth/logout/', { method: 'POST' });
      setUser(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async (overrideMessage?: string) => {
    const userMessage = overrideMessage || input.trim();
    if (!userMessage || loading) return;

    if (!overrideMessage) setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await apiFetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, message: userMessage }),
      });

      const data = await response.json();
      console.log(data);
      if (data.error) {
        setMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${data.error}` }]);
      } else {
        setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
        setStage(data.session.stage);
        if (data.pdfPath) {
          setPdfPath(data.pdfPath);
        }
      }
    } catch (error) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Connection error. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Send to OCR Upload API
      const res = await apiFetch('/api/ocr/upload/', {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (data.text) {
        // 2. Send extracted text to chat with unified prefix
        sendMessage(`EXTRACTED_DOC_DATA: ${data.text}`);
      } else {
        alert('OCR failed to extract text. Please try or type manually.');
      }
    } catch (error) {
      console.error('File upload error:', error);
      alert('Error uploading file.');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  if (authChecking) {
    return (
      <div className="flex items-center justify-center h-screen bg-zinc-50 dark:bg-zinc-950">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) {
    return <LoginSignup onAuthSuccess={(userData) => setUser(userData)} />;
  }

  return (
    <div className="flex flex-col h-screen bg-zinc-50 dark:bg-zinc-950 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white dark:bg-zinc-900 border-b border-zinc-200 dark:border-zinc-800 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-lg ring-2 ring-indigo-500/20">
            A
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-zinc-900 dark:text-zinc-100 tracking-tight">Loan Assistant</h1>
              <span className="text-zinc-300 dark:text-zinc-700">|</span>
              <div className="flex items-center gap-1.5 text-xs text-zinc-500">
                <UserIcon size={12} />
                <span>{user.name}</span>
              </div>
            </div>
            <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400 capitalize flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${stage === 'done' ? 'bg-green-500' : stage === 'kyc' || stage === 'credit' ? 'bg-amber-500' : 'bg-indigo-500'} animate-pulse`} />
              Stage: {stage}
              {pdfPath && (
                <a
                  href={pdfPath.startsWith('/media/') ? `${API_BASE}${pdfPath}` : pdfPath}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-2 text-indigo-400 hover:text-indigo-300 underline"
                >
                  View PDF
                </a>
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden sm:block px-3 py-1 bg-zinc-100 dark:bg-zinc-800 rounded-full text-[10px] font-mono text-zinc-500 dark:text-zinc-500">
            ID: {sessionId}
          </div>
          <button
            onClick={handleLogout}
            className="p-2 text-zinc-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-lg transition-colors"
            title="Logout"
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>

      {/* Chat History */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 scroll-smooth"
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 max-w-sm mx-auto animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <div className="w-16 h-16 rounded-3xl bg-indigo-50 dark:bg-indigo-950/30 flex items-center justify-center text-3xl mb-2 shadow-inner">👋</div>
            <h2 className="text-xl font-bold text-zinc-800 dark:text-zinc-200">Hello {user.name.split(' ')[0]}!</h2>
            <p className="text-zinc-500 dark:text-zinc-400 text-sm leading-relaxed">
              I'm your Loan Assistant. I can help you check your loan eligibility in minutes. Let's start with your basic details.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}
          >
            <div
              className={`max-w-[85%] px-5 py-3.5 rounded-2xl shadow-sm text-sm leading-relaxed ${msg.role === 'user'
                ? 'bg-indigo-600 text-white rounded-tr-none'
                : 'bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-800 rounded-tl-none'
                }`}
            >
              <div className="whitespace-pre-wrap max-w-none">
                <ReactMarkdown
                  components={{
                    a: ({ node, ...props }) => {
                      // Auto-prepend base URL for relative PDF links
                      const href = props.href || '';
                      const fullHref = href.startsWith('/media/')
                        ? `${API_BASE}${href}`
                        : href;

                      return (
                        <a
                          {...props}
                          href={fullHref}
                          className="text-indigo-600 dark:text-indigo-400 underline hover:text-indigo-800 dark:hover:text-indigo-300 transition-colors"
                          target="_blank"
                          rel="noopener noreferrer"
                        />
                      );
                    },
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 px-5 py-3.5 rounded-2xl rounded-tl-none shadow-sm flex gap-1.5 items-center">
              <div className="w-1.5 h-1.5 rounded-full bg-zinc-400 dark:bg-zinc-600 animate-bounce [animation-delay:-0.3s]" />
              <div className="w-1.5 h-1.5 rounded-full bg-zinc-400 dark:bg-zinc-600 animate-bounce [animation-delay:-0.15s]" />
              <div className="w-1.5 h-1.5 rounded-full bg-zinc-400 dark:bg-zinc-600 animate-bounce" />
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 bg-white dark:bg-zinc-900 border-t border-zinc-200 dark:border-zinc-800 shadow-[0_-4px_12px_rgba(0,0,0,0.03)]">
        <div className="max-w-4xl mx-auto flex gap-3 relative">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept="image/*"
            onChange={handleFileUpload}
          />
          <button
            className="p-4 bg-zinc-100 dark:bg-zinc-800 text-zinc-500 rounded-2xl hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all flex items-center justify-center gap-2"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading || loading}
            title="Upload Document (ID or Salary Slip)"
          >
            {uploading ? <Loader2 className="animate-spin" size={20} /> : <div className="flex items-center gap-1"><ImagePlus size={20} /><span className="text-[10px] font-bold">UPLOAD DOC</span></div>}
          </button>
          <input
            className="flex-1 px-5 py-4 bg-zinc-50 dark:bg-zinc-800 border-none rounded-2xl focus:ring-2 focus:ring-indigo-500/20 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-600 text-sm transition-all"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          />
          <button
            className={`px-6 py-2 rounded-2xl font-bold text-sm transition-all flex items-center justify-center gap-2 ${loading
              ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-400 cursor-not-allowed'
              : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-indigo-600/20'
              }`}
            onClick={() => sendMessage()}
            disabled={loading}
          >
            Send
          </button>
        </div>
        <p className="text-[10px] text-zinc-400 text-center mt-3 uppercase tracking-widest font-semibold">Loan Assistant</p>
      </div>
    </div>
  );
}
