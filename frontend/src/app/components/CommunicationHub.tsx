import React, { useState, useEffect, useRef, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import {
  MessageCircle,
  Megaphone,
  Users,
  HelpCircle,
  Send,
  Search,
  Bell,
  Pin,
  ChevronUp,
  ChevronDown,
  User,
  Mail,
  Clock,
  AlertCircle,
  CheckCircle,
  MessageSquare,
  Plus,
  X,
  MoreVertical
} from 'lucide-react';

interface Message {
  id: string;
  sender: {
    id: number;
    username: string;
    full_name: string;
  };
  recipient: {
    id: number;
    username: string;
    full_name: string;
  };
  content: string;
  created_at: string;
  status: string;
  is_from_current_user: boolean;
  time_ago: string;
}

interface Conversation {
  user: {
    id: number;
    username: string;
    full_name: string;
    email?: string;
    has_account?: boolean;
  };
  latest_message: Message | null;
  unread_count: number;
}

interface Announcement {
  id: string;
  title: string;
  content: string;
  priority: string;
  announcement_type: string;
  author: {
    id: number;
    username: string;
    full_name: string;
  };
  time_ago: string;
  is_read: boolean;
}

interface ForumThread {
  id: string;
  title: string;
  content: string;
  category: string;
  author: {
    id: number;
    username: string;
    full_name: string;
  };
  reply_count: number;
  is_pinned: boolean;
  created_at: string;
}

interface QAQuestion {
  id: string;
  question: string;
  session_name?: string;
  author: {
    id: number;
    username: string;
    full_name: string;
  };
  status: string;
  upvotes: number;
  is_anonymous: boolean;
  created_at: string;
  answers?: QAAnswer[];
}

interface QAAnswer {
  id: string;
  answer: string;
  author: {
    id: number;
    username: string;
    full_name: string;
  };
  is_official: boolean;
  created_at: string;
}

interface CommunicationHubProps {
  eventId: string;
}

export const CommunicationHub: React.FC<CommunicationHubProps> = ({ eventId }) => {
  const { token } = useContext(AuthContext);

  if (!token) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 text-center mb-2">Authentication Required</h2>
          <p className="text-gray-600 text-center">Please log in to access the communication hub.</p>
        </div>
      </div>
    );
  }

  const [activeTab, setActiveTab] = useState<'messages' | 'announcements' | 'forum' | 'qa'>('messages');
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [announcementsPagination, setAnnouncementsPagination] = useState({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    currentPage: 1,
    totalPages: 1,
    isLoading: false,
    isLoadingMore: false,
  });
  const [forumThreads, setForumThreads] = useState<ForumThread[]>([]);
  const [qaQuestions, setQAQuestions] = useState<QAQuestion[]>([]);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [showUserList, setShowUserList] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [newThreadTitle, setNewThreadTitle] = useState('');
  const [newThreadContent, setNewThreadContent] = useState('');
  const [newQuestion, setNewQuestion] = useState('');
  const [showNewThreadForm, setShowNewThreadForm] = useState(false);
  const [showNewQuestionForm, setShowNewQuestionForm] = useState(false);
  const [showNewAnnouncementForm, setShowNewAnnouncementForm] = useState(false);
  const [newAnnouncementTitle, setNewAnnouncementTitle] = useState('');
  const [newAnnouncementContent, setNewAnnouncementContent] = useState('');
  const [newAnnouncementPriority, setNewAnnouncementPriority] = useState('normal');
  const [newAnnouncementType, setNewAnnouncementType] = useState('general');
  const [loading, setLoading] = useState(false);
  const [isSubmittingAnnouncement, setIsSubmittingAnnouncement] = useState(false);
  const [isSubmittingThread, setIsSubmittingThread] = useState(false);
  const [isSubmittingQuestion, setIsSubmittingQuestion] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const WS_BASE = API_BASE.replace('http', 'ws');

  // Tab configuration with icons
  const tabs = [
    { id: 'messages', label: 'Messages', icon: MessageCircle },
    { id: 'announcements', label: 'Announcements', icon: Megaphone },
    { id: 'forum', label: 'Forum', icon: Users },
    { id: 'qa', label: 'Q&A', icon: HelpCircle },
  ];

  // Scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Show success message temporarily
  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  // Show error message temporarily
  const showError = (message: string) => {
    setError(message);
    setTimeout(() => setError(null), 5000);
  };

  // Fetch conversations for this event
  const fetchConversations = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/communication/messages/conversations/?event_id=${eventId}`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConversations(data);
      }
    } catch (err) {
      console.error('Error fetching conversations:', err);
    }
  };

  // Fetch messages for a conversation
  const fetchMessages = async (userId: number) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/communication/messages/with_user/?user_id=${userId}&event_id=${eventId}`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setMessages(data.results || data);
      }
    } catch (err) {
      console.error('Error fetching messages:', err);
      showError('Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  // Fetch announcements
  const fetchAnnouncements = async (page: number = 1, append: boolean = false) => {
    if (page === 1) {
      setAnnouncementsPagination(prev => ({ ...prev, isLoading: true }));
    } else {
      setAnnouncementsPagination(prev => ({ ...prev, isLoadingMore: true }));
    }

    try {
      const response = await fetch(`${API_BASE}/api/communication/announcements/?event_id=${eventId}&page=${page}`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();

        // Handle paginated response
        const newAnnouncements = data.results || data;

        if (append && page > 1) {
          // Append to existing announcements for "load more"
          setAnnouncements(prev => [...prev, ...newAnnouncements]);
        } else {
          // Replace announcements for first page or refresh
          setAnnouncements(newAnnouncements);
        }

        // Update pagination metadata
        setAnnouncementsPagination(prev => ({
          ...prev,
          count: data.count || newAnnouncements.length,
          next: data.next,
          previous: data.previous,
          currentPage: page,
          totalPages: data.count ? Math.ceil(data.count / 20) : 1, // 20 is the page size from backend
          isLoading: false,
          isLoadingMore: false,
        }));
      }
    } catch (err) {
      console.error('Error fetching announcements:', err);
      setAnnouncementsPagination(prev => ({
        ...prev,
        isLoading: false,
        isLoadingMore: false
      }));
    }
  };

  // Fetch forum threads
  const fetchForumThreads = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/communication/forum/threads/?event_id=${eventId}`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setForumThreads(data.results || data);
      }
    } catch (err) {
      console.error('Error fetching forum threads:', err);
    }
  };

  // Fetch Q&A questions
  const fetchQAQuestions = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/communication/qa/questions/?event_id=${eventId}`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setQAQuestions(data.results || data);
      }
    } catch (err) {
      console.error('Error fetching Q&A questions:', err);
    }
  };

  // Fetch available users
  const fetchAvailableUsers = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/communication/messages/event_attendees/?event_id=${eventId}`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAvailableUsers(data);
      }
    } catch (err) {
      console.error('Error fetching available users:', err);
    }
  };

  // Send message
  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;

    try {
      const requestBody: any = {
        content: newMessage.trim(),
        event: eventId,
      };

      if (selectedConversation.user.has_account && selectedConversation.user.id) {
        requestBody.recipient_id = selectedConversation.user.id;
      } else {
        requestBody.recipient_email = selectedConversation.user.email;
      }

      const response = await fetch(`${API_BASE}/api/communication/messages/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (response.ok) {
        const newMsg = await response.json();
        setMessages(prev => [newMsg, ...prev]);
        setNewMessage('');

        if (!selectedConversation.user.has_account) {
          showSuccess(`Message sent via email to ${selectedConversation.user.full_name}`);
        }

        if (selectedConversation.user.has_account && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: 'chat_message',
            message: newMessage.trim(),
            recipient_id: selectedConversation.user.id,
          }));
        }
      } else {
        const errorData = await response.json();
        showError(errorData.detail || errorData.error || 'Failed to send message');
      }
    } catch (err) {
      console.error('Error sending message:', err);
      showError('Failed to send message');
    }
  };

  // Mark announcement as read
  const markAnnouncementRead = async (announcementId: string) => {
    try {
      await fetch(`${API_BASE}/api/communication/announcements/${announcementId}/mark_read/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      setAnnouncements(prev =>
        prev.map(ann =>
          ann.id === announcementId ? { ...ann, is_read: true } : ann
        )
      );
    } catch (err) {
      console.error('Error marking announcement as read:', err);
    }
  };

  // Create announcement
  const createAnnouncement = async () => {
    if (!newAnnouncementTitle.trim() || !newAnnouncementContent.trim()) {
      showError('Please fill in both title and content');
      return;
    }

    setIsSubmittingAnnouncement(true);

    try {
      const response = await fetch(`${API_BASE}/api/communication/announcements/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: parseInt(eventId),
          title: newAnnouncementTitle.trim(),
          content: newAnnouncementContent.trim(),
          priority: newAnnouncementPriority,
          announcement_type: newAnnouncementType,
        }),
      });

      if (response.ok) {
        setShowNewAnnouncementForm(false);
        setNewAnnouncementTitle('');
        setNewAnnouncementContent('');
        setNewAnnouncementPriority('normal');
        setNewAnnouncementType('general');
        fetchAnnouncements();
        showSuccess('Announcement posted successfully and emails sent to all invitees!');
      } else {
        const errorData = await response.json();
        showError(`Failed to create announcement: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      console.error('Error creating announcement:', err);
      showError('Network error: Could not create announcement');
    } finally {
      setIsSubmittingAnnouncement(false);
    }
  };

  // Initialize WebSocket
  useEffect(() => {
    if (selectedConversation && token && eventId) {
      const wsUrl = `${WS_BASE}/ws/chat/${eventId}/?token=${token}`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'chat_message') {
          setMessages(prev => [data.message, ...prev]);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      return () => {
        wsRef.current?.close();
      };
    }
  }, [selectedConversation, token, WS_BASE, eventId]);

  // Load initial data
  useEffect(() => {
    if (token && eventId) {
      if (activeTab === 'messages') {
        fetchConversations();
        fetchAvailableUsers();
      } else if (activeTab === 'announcements') {
        fetchAnnouncements();
      } else if (activeTab === 'forum') {
        fetchForumThreads();
      } else if (activeTab === 'qa') {
        fetchQAQuestions();
      }
    }
  }, [token, activeTab, eventId]);

  // Load messages when conversation is selected
  useEffect(() => {
    if (selectedConversation) {
      fetchMessages(selectedConversation.user.id);
    }
  }, [selectedConversation]);

  // Start conversation with user
  const startConversationWithUser = (user: any) => {
    const mockConversation = {
      user: {
        id: user.id,
        username: user.username,
        full_name: user.full_name || user.username,
        email: user.email,
        has_account: user.has_account
      },
      latest_message: null,
      unread_count: 0
    };

    setSelectedConversation(mockConversation);
    setMessages([]);
    setShowUserList(false);
  };

  // Get priority styling
  const getPriorityStyles = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-700 border-red-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'normal': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'low': return 'bg-gray-100 text-gray-700 border-gray-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  // Get priority icon
  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return '🚨';
      case 'high': return '⚠️';
      case 'normal': return 'ℹ️';
      case 'low': return '📌';
      default: return '📌';
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-gray-50 via-white to-gray-50">
      {/* Modern Header */}
      <div className="bg-white/80 backdrop-blur-lg shadow-sm border-b border-gray-200">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Communication Hub
              </h1>
              <p className="text-sm text-gray-600 mt-1">Stay connected with event participants</p>
            </div>
            <div className="flex items-center space-x-3">
              <button className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <Bell className="w-5 h-5 text-gray-600" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
              </button>
              <button className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors">
                <Search className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>

          {/* Enhanced Tab Navigation */}
          <div className="flex space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg font-medium transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/25'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {activeTab === 'messages' && (
          <>
            {/* Enhanced Conversations Sidebar */}
            <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
              <div className="p-4 border-b border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>
                  <button
                    onClick={() => setShowUserList(!showUserList)}
                    className="p-2 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-600 transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search conversations..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Conversations List */}
              <div className="flex-1 overflow-y-auto">
                {conversations.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    <MessageCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm">No conversations yet</p>
                    <button
                      onClick={() => setShowUserList(true)}
                      className="mt-3 text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      Start a conversation
                    </button>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-100">
                    {conversations
                      .filter(conv =>
                        searchQuery === '' ||
                        conv.user.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        conv.user.username.toLowerCase().includes(searchQuery.toLowerCase())
                      )
                      .map((conversation) => (
                        <div
                          key={conversation.user.id}
                          onClick={() => setSelectedConversation(conversation)}
                          className={`p-4 cursor-pointer transition-all duration-200 hover:bg-gray-50 ${
                            selectedConversation?.user.id === conversation.user.id
                              ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500'
                              : ''
                          }`}
                        >
                          <div className="flex items-start space-x-3">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold ${
                              conversation.user.has_account
                                ? 'bg-gradient-to-br from-blue-500 to-purple-500'
                                : 'bg-gray-400'
                            }`}>
                              {(conversation.user.full_name || conversation.user.username || 'U').charAt(0).toUpperCase()}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <h3 className="text-sm font-semibold text-gray-900 truncate">
                                  {conversation.user.full_name || conversation.user.username}
                                </h3>
                                {conversation.unread_count > 0 && (
                                  <span className="ml-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs font-bold rounded-full px-2 py-0.5">
                                    {conversation.unread_count}
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-gray-600 truncate mt-0.5">
                                {conversation.latest_message?.content || 'No messages yet'}
                              </p>
                              <p className="text-xs text-gray-400 mt-1 flex items-center">
                                <Clock className="w-3 h-3 mr-1" />
                                {conversation.latest_message?.time_ago || ''}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </div>

              {/* User List Modal */}
              {showUserList && (
                <div className="absolute inset-0 bg-white z-10 flex flex-col">
                  <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                    <h3 className="font-semibold text-gray-900">Select a User</h3>
                    <button
                      onClick={() => setShowUserList(false)}
                      className="p-1 rounded-lg hover:bg-gray-100"
                    >
                      <X className="w-5 h-5 text-gray-600" />
                    </button>
                  </div>
                  <div className="flex-1 overflow-y-auto p-4">
                    {availableUsers.map((user: any, index: number) => (
                      <div
                        key={user.id || `guest-${index}`}
                        onClick={() => startConversationWithUser(user)}
                        className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                      >
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold ${
                          user.has_account
                            ? 'bg-gradient-to-br from-blue-500 to-purple-500'
                            : 'bg-gray-400'
                        }`}>
                          {(user.full_name || user.username || 'U').charAt(0).toUpperCase()}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {user.full_name || user.username}
                          </p>
                          <p className="text-xs text-gray-500 flex items-center">
                            <Mail className="w-3 h-3 mr-1" />
                            {user.email}
                          </p>
                        </div>
                        {!user.has_account && (
                          <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full">
                            Guest
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Enhanced Chat Area */}
            <div className="flex-1 flex flex-col bg-gradient-to-br from-gray-50 to-white">
              {selectedConversation ? (
                <>
                  {/* Chat Header */}
                  <div className="bg-white border-b border-gray-200 px-6 py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold ${
                          selectedConversation.user.has_account
                            ? 'bg-gradient-to-br from-blue-500 to-purple-500'
                            : 'bg-gray-400'
                        }`}>
                          {(selectedConversation.user.full_name || selectedConversation.user.username || 'U').charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <h2 className="text-lg font-semibold text-gray-900">
                            {selectedConversation.user.full_name || selectedConversation.user.username}
                          </h2>
                          {!selectedConversation.user.has_account && (
                            <p className="text-xs text-gray-500 flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              Messages sent via email
                            </p>
                          )}
                        </div>
                      </div>
                      <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
                        <MoreVertical className="w-5 h-5 text-gray-600" />
                      </button>
                    </div>
                  </div>

                  {/* Messages Area */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {loading ? (
                      <div className="flex items-center justify-center h-full">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                      </div>
                    ) : messages.length === 0 ? (
                      <div className="flex flex-col items-center justify-center h-full text-gray-400">
                        <MessageSquare className="w-12 h-12 mb-3" />
                        <p className="text-sm">No messages yet. Start the conversation!</p>
                      </div>
                    ) : (
                      messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${message.is_from_current_user ? 'justify-end' : 'justify-start'}`}
                        >
                          <div className={`group max-w-[70%] ${message.is_from_current_user ? 'items-end' : 'items-start'}`}>
                            <div
                              className={`px-4 py-3 rounded-2xl shadow-sm ${
                                message.is_from_current_user
                                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                                  : 'bg-white text-gray-900 border border-gray-200'
                              }`}
                            >
                              <p className="text-sm leading-relaxed">{message.content}</p>
                            </div>
                            <p className={`text-xs mt-1 px-2 ${
                              message.is_from_current_user ? 'text-right text-gray-500' : 'text-left text-gray-400'
                            }`}>
                              {message.time_ago}
                              {message.is_from_current_user && message.status === 'read' && (
                                <CheckCircle className="w-3 h-3 inline ml-1 text-blue-500" />
                              )}
                            </p>
                          </div>
                        </div>
                      ))
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Message Input */}
                  <div className="bg-white border-t border-gray-200 px-6 py-4">
                    <div className="flex items-center space-x-3">
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          value={newMessage}
                          onChange={(e) => setNewMessage(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              sendMessage();
                            }
                          }}
                          placeholder="Type your message..."
                          className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                        />
                      </div>
                      <button
                        onClick={sendMessage}
                        disabled={!newMessage.trim()}
                        className={`p-3 rounded-xl transition-all duration-200 ${
                          newMessage.trim()
                            ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg shadow-blue-500/25 hover:shadow-xl hover:scale-105'
                            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        <Send className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <div className="bg-gradient-to-br from-blue-100 to-purple-100 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-4">
                      <MessageCircle className="w-12 h-12 text-blue-600" />
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">Select a conversation</h3>
                    <p className="text-gray-600 mb-4">Choose a conversation from the list or start a new one</p>
                    <button
                      onClick={() => setShowUserList(true)}
                      className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200"
                    >
                      Start New Conversation
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === 'announcements' && (
          <div className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-white">
            <div className="max-w-5xl mx-auto p-6">
              {/* Announcements Header */}
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Announcements</h2>
                  <p className="text-gray-600 mt-1">Important updates and information</p>
                </div>
                <button
                  onClick={() => setShowNewAnnouncementForm(true)}
                  className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200"
                >
                  <Plus className="w-4 h-4" />
                  <span>New Announcement</span>
                </button>
              </div>

              {/* New Announcement Form */}
              {showNewAnnouncementForm && (
                <div className="bg-white rounded-2xl shadow-xl p-6 mb-6 border border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Create Announcement</h3>
                  <div className="space-y-4">
                    <input
                      type="text"
                      placeholder="Announcement title..."
                      value={newAnnouncementTitle}
                      onChange={(e) => setNewAnnouncementTitle(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <textarea
                      placeholder="Announcement content..."
                      value={newAnnouncementContent}
                      onChange={(e) => setNewAnnouncementContent(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={4}
                    />
                    <div className="flex space-x-3">
                      <select
                        value={newAnnouncementPriority}
                        onChange={(e) => setNewAnnouncementPriority(e.target.value)}
                        className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="low">Low Priority</option>
                        <option value="normal">Normal Priority</option>
                        <option value="high">High Priority</option>
                        <option value="critical">Critical Priority</option>
                      </select>
                      <select
                        value={newAnnouncementType}
                        onChange={(e) => setNewAnnouncementType(e.target.value)}
                        className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      >
                        <option value="general">General</option>
                        <option value="schedule">Schedule Update</option>
                        <option value="urgent">Urgent</option>
                        <option value="reminder">Reminder</option>
                      </select>
                    </div>
                    <div className="flex space-x-3">
                      <button
                        onClick={createAnnouncement}
                        disabled={isSubmittingAnnouncement || !newAnnouncementTitle.trim() || !newAnnouncementContent.trim()}
                        className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                      >
                        {isSubmittingAnnouncement ? (
                          <>
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            <span>Posting & Sending Emails...</span>
                          </>
                        ) : (
                          <span>Post Announcement</span>
                        )}
                      </button>
                      <button
                        onClick={() => {
                          setShowNewAnnouncementForm(false);
                          setNewAnnouncementTitle('');
                          setNewAnnouncementContent('');
                          setNewAnnouncementPriority('normal');
                          setNewAnnouncementType('general');
                        }}
                        disabled={isSubmittingAnnouncement}
                        className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Announcements List */}
              <div className="space-y-4">
                {announcements.length === 0 ? (
                  <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
                    <Megaphone className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">No announcements yet</p>
                  </div>
                ) : (
                  announcements.map((announcement) => (
                    <div
                      key={announcement.id}
                      className={`bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all duration-200 overflow-hidden ${
                        !announcement.is_read ? 'ring-2 ring-blue-500 ring-offset-2' : ''
                      }`}
                      onClick={() => !announcement.is_read && markAnnouncementRead(announcement.id)}
                    >
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center space-x-3">
                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${getPriorityStyles(announcement.priority)}`}>
                              <span className="mr-1">{getPriorityIcon(announcement.priority)}</span>
                              {announcement.priority.toUpperCase()}
                            </span>
                            <span className="text-xs px-3 py-1 bg-gray-100 text-gray-600 rounded-full">
                              {announcement.announcement_type.replace('_', ' ').toUpperCase()}
                            </span>
                            {!announcement.is_read && (
                              <span className="flex items-center text-xs text-blue-600 font-medium">
                                <span className="w-2 h-2 bg-blue-500 rounded-full mr-1"></span>
                                NEW
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-gray-500 flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {announcement.time_ago}
                          </span>
                        </div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">
                          {announcement.title}
                        </h3>
                        <p className="text-gray-700 leading-relaxed mb-3">
                          {announcement.content}
                        </p>
                        <div className="flex items-center text-sm text-gray-500">
                          <User className="w-4 h-4 mr-1" />
                          <span>{announcement.author.full_name || announcement.author.username}</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Pagination Controls */}
              {!announcementsPagination.isLoading && announcements.length > 0 && (
                <div className="mt-8 flex flex-col items-center space-y-4">
                  {/* Page Info */}
                  <div className="text-sm text-gray-600">
                    Showing {announcements.length} of {announcementsPagination.count} announcements
                    {announcementsPagination.totalPages > 1 && (
                      <span> (Page {announcementsPagination.currentPage} of {announcementsPagination.totalPages})</span>
                    )}
                  </div>

                  {/* Load More Button */}
                  {announcementsPagination.next && (
                    <button
                      onClick={() => fetchAnnouncements(announcementsPagination.currentPage + 1, true)}
                      disabled={announcementsPagination.isLoadingMore}
                      className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                    >
                      {announcementsPagination.isLoadingMore ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          <span>Loading more...</span>
                        </>
                      ) : (
                        <>
                          <span>Load More Announcements</span>
                          <ChevronDown className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  )}

                  {/* Page Navigation (alternative to load more) */}
                  {announcementsPagination.totalPages > 1 && (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => fetchAnnouncements(announcementsPagination.currentPage - 1)}
                        disabled={!announcementsPagination.previous || announcementsPagination.isLoading}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                      >
                        <ChevronUp className="w-4 h-4 mr-1 rotate-[-90deg]" />
                        Previous
                      </button>

                      {/* Page numbers */}
                      <div className="flex items-center space-x-1">
                        {Array.from({ length: Math.min(5, announcementsPagination.totalPages) }, (_, i) => {
                          const pageNum = i + 1;
                          const isCurrentPage = pageNum === announcementsPagination.currentPage;
                          return (
                            <button
                              key={pageNum}
                              onClick={() => fetchAnnouncements(pageNum)}
                              disabled={announcementsPagination.isLoading}
                              className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                                isCurrentPage
                                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-lg'
                                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                              }`}
                            >
                              {pageNum}
                            </button>
                          );
                        })}
                      </div>

                      <button
                        onClick={() => fetchAnnouncements(announcementsPagination.currentPage + 1)}
                        disabled={!announcementsPagination.next || announcementsPagination.isLoading}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                      >
                        Next
                        <ChevronUp className="w-4 h-4 ml-1 rotate-90" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Loading State */}
              {announcementsPagination.isLoading && announcements.length === 0 && (
                <div className="flex items-center justify-center py-12">
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-gray-600">Loading announcements...</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'forum' && (
          <div className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-white">
            <div className="max-w-5xl mx-auto p-6">
              {/* Forum Header */}
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Discussion Forum</h2>
                  <p className="text-gray-600 mt-1">Join the conversation with other attendees</p>
                </div>
                <button
                  onClick={() => setShowNewThreadForm(true)}
                  className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200"
                >
                  <Plus className="w-4 h-4" />
                  <span>New Thread</span>
                </button>
              </div>

              {/* New Thread Form */}
              {showNewThreadForm && (
                <div className="bg-white rounded-2xl shadow-xl p-6 mb-6 border border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Start a Discussion</h3>
                  <div className="space-y-4">
                    <input
                      type="text"
                      placeholder="Thread title..."
                      value={newThreadTitle}
                      onChange={(e) => setNewThreadTitle(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <textarea
                      placeholder="What would you like to discuss?"
                      value={newThreadContent}
                      onChange={(e) => setNewThreadContent(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={5}
                    />
                    <div className="flex space-x-3">
                      <button
                        onClick={async () => {
                          if (!newThreadTitle.trim() || !newThreadContent.trim()) {
                            showError('Please fill in both title and content');
                            return;
                          }

                          setIsSubmittingThread(true);

                          try {
                            const response = await fetch(`${API_BASE}/api/communication/forum/threads/`, {
                              method: 'POST',
                              headers: {
                                'Authorization': `Token ${token}`,
                                'Content-Type': 'application/json',
                              },
                              body: JSON.stringify({
                                event: parseInt(eventId),
                                title: newThreadTitle.trim(),
                                content: newThreadContent.trim(),
                                category: 'general',
                              }),
                            });

                            if (response.ok) {
                              setShowNewThreadForm(false);
                              setNewThreadTitle('');
                              setNewThreadContent('');
                              fetchForumThreads();
                              showSuccess('Thread created successfully');
                            } else {
                              const errorData = await response.json();
                              showError(`Failed to create thread: ${errorData.detail || 'Unknown error'}`);
                            }
                          } catch (err) {
                            console.error('Error creating thread:', err);
                            showError('Network error: Could not create thread');
                          } finally {
                            setIsSubmittingThread(false);
                          }
                        }}
                        disabled={isSubmittingThread || !newThreadTitle.trim() || !newThreadContent.trim()}
                        className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isSubmittingThread ? 'Posting...' : 'Post Thread'}
                      </button>
                      <button
                        onClick={() => {
                          setShowNewThreadForm(false);
                          setNewThreadTitle('');
                          setNewThreadContent('');
                        }}
                        disabled={isSubmittingThread}
                        className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Forum Threads */}
              <div className="space-y-4">
                {forumThreads.length === 0 ? (
                  <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
                    <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">No discussions yet. Be the first to start one!</p>
                  </div>
                ) : (
                  forumThreads.map((thread) => (
                    <div key={thread.id} className="bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all duration-200 p-6 cursor-pointer">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            {thread.is_pinned && (
                              <span className="inline-flex items-center px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded-full">
                                <Pin className="w-3 h-3 mr-1" />
                                Pinned
                              </span>
                            )}
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                              {thread.category}
                            </span>
                          </div>
                          <h3 className="text-lg font-semibold text-gray-900 mb-2">{thread.title}</h3>
                          <p className="text-gray-600 line-clamp-2 mb-3">
                            {thread.content}
                          </p>
                          <div className="flex items-center text-sm text-gray-500 space-x-4">
                            <span className="flex items-center">
                              <User className="w-4 h-4 mr-1" />
                              {thread.author.full_name || thread.author.username}
                            </span>
                            <span className="flex items-center">
                              <MessageSquare className="w-4 h-4 mr-1" />
                              {thread.reply_count} replies
                            </span>
                            <span className="flex items-center">
                              <Clock className="w-4 h-4 mr-1" />
                              {new Date(thread.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'qa' && (
          <div className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-white">
            <div className="max-w-5xl mx-auto p-6">
              {/* Q&A Header */}
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Q&A</h2>
                  <p className="text-gray-600 mt-1">Ask questions and get answers</p>
                </div>
                <button
                  onClick={() => setShowNewQuestionForm(true)}
                  className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200"
                >
                  <Plus className="w-4 h-4" />
                  <span>Ask Question</span>
                </button>
              </div>

              {/* New Question Form */}
              {showNewQuestionForm && (
                <div className="bg-white rounded-2xl shadow-xl p-6 mb-6 border border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Ask a Question</h3>
                  <div className="space-y-4">
                    <textarea
                      placeholder="What would you like to know?"
                      value={newQuestion}
                      onChange={(e) => setNewQuestion(e.target.value)}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                      rows={3}
                    />
                    <div className="flex space-x-3">
                      <button
                        onClick={async () => {
                          if (!newQuestion.trim()) {
                            showError('Please enter a question');
                            return;
                          }

                          setIsSubmittingQuestion(true);

                          try {
                            const response = await fetch(`${API_BASE}/api/communication/qa/questions/`, {
                              method: 'POST',
                              headers: {
                                'Authorization': `Token ${token}`,
                                'Content-Type': 'application/json',
                              },
                              body: JSON.stringify({
                                event: parseInt(eventId),
                                question: newQuestion.trim(),
                              }),
                            });

                            if (response.ok) {
                              setShowNewQuestionForm(false);
                              setNewQuestion('');
                              fetchQAQuestions();
                              showSuccess('Question submitted successfully');
                            } else {
                              const errorData = await response.json();
                              showError(`Failed to submit question: ${errorData.detail || 'Unknown error'}`);
                            }
                          } catch (err) {
                            console.error('Error creating question:', err);
                            showError('Network error: Could not submit question');
                          } finally {
                            setIsSubmittingQuestion(false);
                          }
                        }}
                        disabled={isSubmittingQuestion || !newQuestion.trim()}
                        className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isSubmittingQuestion ? 'Submitting...' : 'Submit Question'}
                      </button>
                      <button
                        onClick={() => {
                          setShowNewQuestionForm(false);
                          setNewQuestion('');
                        }}
                        disabled={isSubmittingQuestion}
                        className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Questions List */}
              <div className="space-y-4">
                {qaQuestions.length === 0 ? (
                  <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
                    <HelpCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">No questions yet. Ask the first one!</p>
                  </div>
                ) : (
                  qaQuestions.map((question) => (
                    <div key={question.id} className="bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all duration-200 p-6">
                      <div className="flex items-start space-x-4">
                        <div className="flex flex-col items-center">
                          <button className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-blue-600 transition-colors">
                            <ChevronUp className="w-5 h-5" />
                          </button>
                          <span className="text-lg font-bold text-gray-700">{question.upvotes}</span>
                        </div>
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-2">
                            <h3 className="text-lg font-semibold text-gray-900 flex-1">
                              {question.question}
                            </h3>
                            <span className={`ml-3 px-3 py-1 rounded-full text-xs font-medium ${
                              question.status === 'answered'
                                ? 'bg-green-100 text-green-700'
                                : question.status === 'approved'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-gray-100 text-gray-700'
                            }`}>
                              {question.status.toUpperCase()}
                            </span>
                          </div>
                          {question.session_name && (
                            <span className="inline-block px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full mb-2">
                              {question.session_name}
                            </span>
                          )}
                          <div className="flex items-center text-sm text-gray-500 mb-3">
                            <User className="w-4 h-4 mr-1" />
                            <span>
                              {question.is_anonymous
                                ? 'Anonymous'
                                : (question.author.full_name || question.author.username)}
                            </span>
                            <span className="mx-2">•</span>
                            <Clock className="w-4 h-4 mr-1" />
                            <span>{new Date(question.created_at).toLocaleDateString()}</span>
                          </div>

                          {question.answers && question.answers.length > 0 && (
                            <div className="mt-4 space-y-3 pl-4 border-l-2 border-gray-200">
                              {question.answers.map((answer) => (
                                <div key={answer.id} className="bg-gray-50 rounded-lg p-4">
                                  {answer.is_official && (
                                    <span className="inline-flex items-center px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full mb-2">
                                      <CheckCircle className="w-3 h-3 mr-1" />
                                      Official Answer
                                    </span>
                                  )}
                                  <p className="text-gray-700 mb-2">{answer.answer}</p>
                                  <p className="text-xs text-gray-500">
                                    <span className="font-medium">
                                      {answer.author.full_name || answer.author.username}
                                    </span>
                                    <span className="mx-2">•</span>
                                    {new Date(answer.created_at).toLocaleDateString()}
                                  </p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Toast Notifications */}
      {(error || successMessage) && (
        <div className={`fixed bottom-6 right-6 max-w-sm ${error ? 'bg-red-500' : 'bg-green-500'} text-white px-6 py-4 rounded-xl shadow-2xl flex items-center space-x-3 animate-slide-up`}>
          {error ? (
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
          ) : (
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
          )}
          <p className="text-sm font-medium">{error || successMessage}</p>
          <button
            onClick={() => {
              setError(null);
              setSuccessMessage(null);
            }}
            className="ml-auto text-white/80 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <style>{`
        @keyframes slide-up {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .animate-slide-up {
          animation: slide-up 0.3s ease-out;
        }
        .line-clamp-2 {
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
      `}</style>
    </div>
  );
};