'use client';
import { useUser, UserButton } from '@clerk/react';
import ReactMarkdown from 'react-markdown';
import { useState, useEffect, useRef } from 'react';
import LoginSignup from '../components/react-login-signup';
import { apiFetch, API_BASE } from '../api';
import { User as UserIcon, ImagePlus, Loader2 } from 'lucide-react';
import './react-home.css';

export default function Home() {
  const { isLoaded, isSignedIn, user } = useUser();
  const [sessionId, setSessionId] = useState('');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [stage, setStage] = useState('sales');
  const [pdfPath, setPdfPath] = useState(null);
  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    setSessionId(`session_${Math.random().toString(36).substring(7)}`);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async (overrideMessage) => {
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

  const handleFileUpload = async (event) => {
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

  if (!isLoaded) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!isSignedIn) {
    return <LoginSignup />;
  }

  const displayName = user?.fullName || user?.firstName || user?.primaryEmailAddress?.emailAddress || 'User';
  const firstName = user?.firstName || displayName.split(' ')[0] || 'there';

  return (
    <div className="home-container">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="header-avatar">
            A
          </div>
          <div>
            <div className="header-title-row">
              <h1 className="header-title">Loan Assistant</h1>
              <span className="header-divider">|</span>
              <div className="header-user-info">
                <UserIcon size={12} />
                <span>{displayName}</span>
              </div>
            </div>
            <p className="header-stage-info">
              <span
                className={`stage-dot ${
                  stage === 'done'
                    ? 'stage-dot-done'
                    : stage === 'kyc' || stage === 'credit'
                    ? 'stage-dot-pending'
                    : ''
                }`}
              />
              Stage: {stage}
              {pdfPath && (
                <a
                  href={pdfPath.startsWith('/media/') ? `${API_BASE}${pdfPath}` : pdfPath}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="header-pdf-link"
                >
                  View PDF
                </a>
              )}
            </p>
          </div>
        </div>
        <div className="header-right">
          <div className="session-pill">
            ID: {sessionId}
          </div>
          <UserButton />
        </div>
      </header>

      {/* Chat History */}
      <div ref={scrollRef} className="chat-history">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <div className="chat-welcome-icon">👋</div>
            <h2 className="chat-welcome-title">Hello {firstName}!</h2>
            <p className="chat-welcome-text">
              I'm your Loan Assistant. I can help you check your loan eligibility in minutes. Let's start with your basic details.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`message-row ${
              msg.role === 'user' ? 'message-row-user' : 'message-row-assistant'
            }`}
          >
            <div
              className={`message-bubble ${
                msg.role === 'user' ? 'message-bubble-user' : 'message-bubble-assistant'
              }`}
            >
              <div className="markdown-content">
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
                          className="markdown-link"
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
          <div className="typing-row">
            <div className="typing-bubble">
              <div className="typing-dot typing-dot-1" />
              <div className="typing-dot typing-dot-2" />
              <div className="typing-dot" />
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-area-container">
        <div className="input-bar">
          <input
            type="file"
            ref={fileInputRef}
            className="file-input-hidden"
            accept="image/*"
            onChange={handleFileUpload}
          />
          <button
            className="upload-doc-btn"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading || loading}
            title="Upload Document (ID or Salary Slip)"
          >
            {uploading ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <div className="upload-doc-label">
                <ImagePlus size={20} />
                <span className="upload-doc-text">UPLOAD DOC</span>
              </div>
            )}
          </button>
          <input
            className="chat-text-input"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          />
          <button
            className={`send-button ${
              loading ? 'send-button-disabled' : 'send-button-active'
            }`}
            onClick={() => sendMessage()}
            disabled={loading}
          >
            Send
          </button>
        </div>
        <p className="footer-caption">Loan Assistant</p>
      </div>
    </div>
  );
}
