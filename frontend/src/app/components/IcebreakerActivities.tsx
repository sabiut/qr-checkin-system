import React, { useState, useEffect } from 'react';
import {
  Heart,
  MessageSquare,
  Clock,
  User,
  Trophy,
  Eye,
  Star,
  Send,
  Plus,
  X,
  AlertCircle,
  CheckCircle,
  Gamepad2,
  Users,
  Activity,
  BarChart3,
  Download,
  UserCheck,
  Mail,
  Calendar
} from 'lucide-react';

interface IcebreakerActivity {
  id: string;
  title: string;
  description: string;
  activity_type: 'poll' | 'quiz' | 'question' | 'challenge' | 'introduction';
  activity_data: any;
  is_featured: boolean;
  allow_multiple_responses: boolean;
  anonymous_responses: boolean;
  creator: {
    id: number;
    username: string;
    full_name: string;
  };
  response_count: number;
  view_count: number;
  points_reward: number;
  time_ago: string;
  has_responded: boolean;
  starts_at?: string;
  ends_at?: string;
}

interface IcebreakerResponse {
  id: string;
  user_name: string;
  response_data: any;
  like_count: number;
  reply_count: number;
  time_ago: string;
  is_guest_response: boolean;
  guest_email?: string;
  guest_name?: string;
  created_at: string;
}

interface IcebreakerActivitiesProps {
  eventId: string;
  token: string;
  showError: (message: string) => void;
  showSuccess: (message: string) => void;
}

export const IcebreakerActivities: React.FC<IcebreakerActivitiesProps> = ({
  eventId,
  token,
  showError,
  showSuccess
}) => {
  const [activities, setActivities] = useState<IcebreakerActivity[]>([]);
  const [selectedActivity, setSelectedActivity] = useState<IcebreakerActivity | null>(null);
  const [responses, setResponses] = useState<IcebreakerResponse[]>([]);
  const [newResponseData, setNewResponseData] = useState<any>({});
  const [loading, setLoading] = useState(false);
  const [isSubmittingResponse, setIsSubmittingResponse] = useState(false);
  const [showResponseForm, setShowResponseForm] = useState(false);
  const [activeTab, setActiveTab] = useState<'respond' | 'analytics'>('respond');
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [isCreatingActivity, setIsCreatingActivity] = useState(false);
  const [filter, setFilter] = useState<'all' | 'featured' | 'upcoming'>('all');

  // New activity form state
  const [newActivity, setNewActivity] = useState({
    title: '',
    description: '',
    activity_type: 'question' as 'poll' | 'quiz' | 'question' | 'challenge' | 'introduction',
    activity_data: {} as any,
    is_featured: false,
    points_reward: 5,
  });

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Fetch activities
  const fetchActivities = async () => {
    try {
      setLoading(true);
      let url = `${API_BASE}/api/communication/icebreakers/?event_id=${eventId}`;

      if (filter === 'featured') {
        url += '&featured=true';
      } else if (filter === 'upcoming') {
        url += '&upcoming=true';
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setActivities(data.results || data);
      }
    } catch (err) {
      console.error('Error fetching icebreaker activities:', err);
      showError('Failed to load icebreaker activities');
    } finally {
      setLoading(false);
    }
  };

  // Fetch responses for an activity
  const fetchResponses = async (activityId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/communication/icebreakers/${activityId}/responses/`, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setResponses(data.results || data);
      }
    } catch (err) {
      console.error('Error fetching responses:', err);
    }
  };

  // Submit response
  const submitResponse = async (activityId: string) => {
    if (!newResponseData || Object.keys(newResponseData).length === 0) {
      showError('Please provide a response');
      return;
    }

    setIsSubmittingResponse(true);

    try {
      const response = await fetch(`${API_BASE}/api/communication/icebreakers/${activityId}/respond/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          response_data: newResponseData,
          is_public: true,
        }),
      });

      if (response.ok) {
        const responseData = await response.json();
        setNewResponseData({});
        setShowResponseForm(false);
        fetchActivities(); // Refresh to update response counts
        if (selectedActivity) {
          fetchResponses(selectedActivity.id);
        }
        showSuccess(`Response submitted! You earned ${selectedActivity?.points_reward || 0} points!`);
      } else {
        const errorData = await response.json();
        showError(errorData.error || 'Failed to submit response');
      }
    } catch (err) {
      console.error('Error submitting response:', err);
      showError('Network error: Could not submit response');
    } finally {
      setIsSubmittingResponse(false);
    }
  };

  // Create new activity
  const createActivity = async () => {
    if (!newActivity.title.trim() || !newActivity.description.trim()) {
      showError('Please fill in title and description');
      return;
    }

    setIsCreatingActivity(true);

    try {
      // Prepare activity data based on type
      let activityData = {};

      if (newActivity.activity_type === 'poll') {
        const options = newActivity.activity_data.options?.filter((opt: string) => opt.trim()) || [];
        if (options.length < 2) {
          showError('Poll must have at least 2 options');
          setIsCreatingActivity(false);
          return;
        }
        activityData = {
          question: newActivity.activity_data.question || newActivity.title,
          options: options
        };
      } else if (newActivity.activity_type === 'quiz') {
        const options = newActivity.activity_data.options?.filter((opt: string) => opt.trim()) || [];
        if (options.length < 2 || !newActivity.activity_data.correct_answer) {
          showError('Quiz must have at least 2 options and a correct answer');
          setIsCreatingActivity(false);
          return;
        }
        activityData = {
          question: newActivity.activity_data.question || newActivity.title,
          options: options,
          correct_answer: newActivity.activity_data.correct_answer
        };
      }

      const response = await fetch(`${API_BASE}/api/communication/icebreakers/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: parseInt(eventId),
          title: newActivity.title.trim(),
          description: newActivity.description.trim(),
          activity_type: newActivity.activity_type,
          activity_data: activityData,
          is_featured: newActivity.is_featured,
          points_reward: newActivity.points_reward,
          is_active: true,
          allow_multiple_responses: false,
          anonymous_responses: false,
        }),
      });

      if (response.ok) {
        const createdActivity = await response.json();
        setShowCreateForm(false);
        setNewActivity({
          title: '',
          description: '',
          activity_type: 'question',
          activity_data: {},
          is_featured: false,
          points_reward: 5,
        });
        fetchActivities(); // Refresh activities list
        showSuccess('Icebreaker activity created successfully!');
      } else {
        const errorData = await response.json();
        showError(errorData.detail || errorData.error || 'Failed to create activity');
      }
    } catch (err) {
      console.error('Error creating activity:', err);
      showError('Network error: Could not create activity');
    } finally {
      setIsCreatingActivity(false);
    }
  };

  // Get activity type icon
  const getActivityTypeIcon = (type: string) => {
    switch (type) {
      case 'poll': return <Activity className="w-5 h-5" />;
      case 'quiz': return <Trophy className="w-5 h-5" />;
      case 'question': return <MessageSquare className="w-5 h-5" />;
      case 'challenge': return <Gamepad2 className="w-5 h-5" />;
      case 'introduction': return <Users className="w-5 h-5" />;
      default: return <Heart className="w-5 h-5" />;
    }
  };

  // Get activity type color
  const getActivityTypeColor = (type: string) => {
    switch (type) {
      case 'poll': return 'bg-blue-100 text-blue-700';
      case 'quiz': return 'bg-yellow-100 text-yellow-700';
      case 'question': return 'bg-green-100 text-green-700';
      case 'challenge': return 'bg-red-100 text-red-700';
      case 'introduction': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  // Render response form based on activity type
  const renderResponseForm = (activity: IcebreakerActivity) => {
    switch (activity.activity_type) {
      case 'poll':
        return (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">Choose your option:</p>
            {activity.activity_data.options?.map((option: string, index: number) => (
              <label key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                <input
                  type="radio"
                  name="poll_option"
                  value={option}
                  checked={newResponseData.selected_option === option}
                  onChange={(e) => setNewResponseData({ selected_option: e.target.value })}
                  className="text-blue-600 focus:ring-blue-500"
                />
                <span className="text-gray-900">{option}</span>
              </label>
            ))}
          </div>
        );

      case 'quiz':
        return (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">Answer the question:</p>
            <p className="font-medium text-gray-900">{activity.activity_data.question}</p>
            {activity.activity_data.options?.map((option: string, index: number) => (
              <label key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                <input
                  type="radio"
                  name="quiz_answer"
                  value={option}
                  checked={newResponseData.selected_answer === option}
                  onChange={(e) => setNewResponseData({ selected_answer: e.target.value })}
                  className="text-blue-600 focus:ring-blue-500"
                />
                <span className="text-gray-900">{option}</span>
              </label>
            ))}
          </div>
        );

      default:
        return (
          <div className="space-y-3">
            <p className="text-sm text-gray-600">Share your response:</p>
            <textarea
              value={newResponseData.text_response || ''}
              onChange={(e) => setNewResponseData({ text_response: e.target.value })}
              placeholder="Write your response here..."
              className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={4}
            />
          </div>
        );
    }
  };

  // Load activities on component mount and filter change
  useEffect(() => {
    if (token && eventId) {
      fetchActivities();
    }
  }, [token, eventId, filter]);

  // Calculate analytics data from responses
  const calculateAnalytics = (responses: IcebreakerResponse[]) => {
    const totalResponses = responses.length;
    const guestResponses = responses.filter(r => r.is_guest_response).length;
    const registeredResponses = totalResponses - guestResponses;

    // Response distribution for polls/quizzes
    const responseDistribution: { [key: string]: number } = {};
    responses.forEach(response => {
      if (response.response_data.selected_option) {
        const option = response.response_data.selected_option;
        responseDistribution[option] = (responseDistribution[option] || 0) + 1;
      }
    });

    return {
      totalResponses,
      guestResponses,
      registeredResponses,
      responseDistribution,
      responseRate: selectedActivity ? Math.round((totalResponses / Math.max(selectedActivity.view_count, 1)) * 100) : 0
    };
  };

  // Export responses to CSV
  const exportResponses = () => {
    if (!responses.length || !selectedActivity) return;

    const csvContent = [
      // Header
      ['Name', 'Type', 'Email', 'Response', 'Date', 'Time'].join(','),
      // Data rows
      ...responses.map(response => [
        response.user_name,
        response.is_guest_response ? 'Guest' : 'Registered',
        response.guest_email || '',
        response.response_data.text || response.response_data.selected_option || 'No response',
        new Date(response.created_at).toLocaleDateString(),
        new Date(response.created_at).toLocaleTimeString()
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `icebreaker_responses_${selectedActivity.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Load responses and calculate analytics when activity is selected
  useEffect(() => {
    if (selectedActivity) {
      fetchResponses(selectedActivity.id);
      setActiveTab('respond'); // Reset to respond tab when switching activities
    }
  }, [selectedActivity]);

  // Update analytics when responses change
  useEffect(() => {
    if (responses.length > 0) {
      setAnalyticsData(calculateAnalytics(responses));
    }
  }, [responses]);

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-br from-gray-50 to-white">
      <div className="max-w-6xl mx-auto p-6">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Icebreaker Activities</h2>
            <p className="text-gray-600 mt-1">Connect with other attendees through fun activities</p>
          </div>

          <div className="flex items-center space-x-3">
            {/* Create Activity Button */}
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-medium shadow-lg shadow-green-500/25 hover:shadow-xl transition-all duration-200"
            >
              <Plus className="w-4 h-4" />
              <span>Create Activity</span>
            </button>

            {/* Filter Buttons */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setFilter('all')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  filter === 'all'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setFilter('featured')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  filter === 'featured'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Featured
              </button>
              <button
                onClick={() => setFilter('upcoming')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  filter === 'upcoming'
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Upcoming
              </button>
            </div>
          </div>
        </div>

        {/* Create Activity Form */}
        {showCreateForm && (
          <div className="mb-6 bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Create New Icebreaker Activity</h3>
              <button
                onClick={() => {
                  setShowCreateForm(false);
                  setNewActivity({
                    title: '',
                    description: '',
                    activity_type: 'question',
                    activity_data: {},
                    is_featured: false,
                    points_reward: 5,
                  });
                }}
                className="p-1 rounded-lg hover:bg-gray-100 text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Basic Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Activity Title</label>
                  <input
                    type="text"
                    value={newActivity.title}
                    onChange={(e) => setNewActivity({ ...newActivity, title: e.target.value })}
                    placeholder="e.g., Welcome Poll: What excites you most?"
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Activity Type</label>
                  <select
                    value={newActivity.activity_type}
                    onChange={(e) => setNewActivity({
                      ...newActivity,
                      activity_type: e.target.value as any,
                      activity_data: {} // Reset activity data when type changes
                    })}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="question">Open Question</option>
                    <option value="poll">Poll (Multiple Choice)</option>
                    <option value="quiz">Quiz (Right/Wrong Answer)</option>
                    <option value="introduction">Introduction</option>
                    <option value="challenge">Challenge</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  value={newActivity.description}
                  onChange={(e) => setNewActivity({ ...newActivity, description: e.target.value })}
                  placeholder="Describe what this activity is about and how attendees should participate..."
                  className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                  rows={3}
                />
              </div>

              {/* Activity-specific fields */}
              {(newActivity.activity_type === 'poll' || newActivity.activity_type === 'quiz') && (
                <div className="space-y-3">
                  <label className="block text-sm font-medium text-gray-700">
                    {newActivity.activity_type === 'poll' ? 'Poll Question (optional)' : 'Quiz Question'}
                  </label>
                  <input
                    type="text"
                    value={newActivity.activity_data.question || ''}
                    onChange={(e) => setNewActivity({
                      ...newActivity,
                      activity_data: { ...newActivity.activity_data, question: e.target.value }
                    })}
                    placeholder={`Enter your ${newActivity.activity_type} question...`}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />

                  <label className="block text-sm font-medium text-gray-700">Options</label>
                  {(newActivity.activity_data.options || ['', '']).map((option: string, index: number) => (
                    <div key={index} className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={option}
                        onChange={(e) => {
                          const newOptions = [...(newActivity.activity_data.options || ['', ''])];
                          newOptions[index] = e.target.value;
                          setNewActivity({
                            ...newActivity,
                            activity_data: { ...newActivity.activity_data, options: newOptions }
                          });
                        }}
                        placeholder={`Option ${index + 1}`}
                        className="flex-1 px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                      {index > 1 && (
                        <button
                          onClick={() => {
                            const newOptions = [...(newActivity.activity_data.options || [])];
                            newOptions.splice(index, 1);
                            setNewActivity({
                              ...newActivity,
                              activity_data: { ...newActivity.activity_data, options: newOptions }
                            });
                          }}
                          className="p-2 text-red-500 hover:bg-red-50 rounded-lg"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => {
                      const currentOptions = newActivity.activity_data.options || ['', ''];
                      setNewActivity({
                        ...newActivity,
                        activity_data: { ...newActivity.activity_data, options: [...currentOptions, ''] }
                      });
                    }}
                    className="text-green-600 hover:text-green-700 text-sm font-medium flex items-center"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Add Option
                  </button>

                  {newActivity.activity_type === 'quiz' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Correct Answer</label>
                      <select
                        value={newActivity.activity_data.correct_answer || ''}
                        onChange={(e) => setNewActivity({
                          ...newActivity,
                          activity_data: { ...newActivity.activity_data, correct_answer: e.target.value }
                        })}
                        className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      >
                        <option value="">Select the correct answer</option>
                        {(newActivity.activity_data.options || []).map((option: string, index: number) => (
                          option.trim() && (
                            <option key={index} value={option}>
                              {option}
                            </option>
                          )
                        ))}
                      </select>
                    </div>
                  )}
                </div>
              )}

              {/* Settings */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Points Reward</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={newActivity.points_reward}
                    onChange={(e) => setNewActivity({ ...newActivity, points_reward: parseInt(e.target.value) || 5 })}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-900 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  />
                </div>

                <div className="flex items-center">
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={newActivity.is_featured}
                      onChange={(e) => setNewActivity({ ...newActivity, is_featured: e.target.checked })}
                      className="w-5 h-5 text-green-600 bg-gray-100 border-gray-300 rounded focus:ring-green-500"
                    />
                    <span className="text-sm font-medium text-gray-700">Featured Activity</span>
                    <Star className="w-4 h-4 text-yellow-500" />
                  </label>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3 pt-4">
                <button
                  onClick={createActivity}
                  disabled={isCreatingActivity || !newActivity.title.trim() || !newActivity.description.trim()}
                  className="flex-1 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-medium shadow-lg shadow-green-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isCreatingActivity ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Creating...</span>
                    </>
                  ) : (
                    <>
                      <Activity className="w-4 h-4" />
                      <span>Create Activity</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewActivity({
                      title: '',
                      description: '',
                      activity_type: 'question',
                      activity_data: {},
                      is_featured: false,
                      points_reward: 5,
                    });
                  }}
                  disabled={isCreatingActivity}
                  className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Activities List */}
          <div className="lg:col-span-2 space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-gray-600">Loading activities...</span>
                </div>
              </div>
            ) : activities.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
                <Heart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No icebreaker activities yet</p>
              </div>
            ) : (
              activities.map((activity) => (
                <div
                  key={activity.id}
                  onClick={() => setSelectedActivity(activity)}
                  className={`bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all duration-200 cursor-pointer overflow-hidden ${
                    selectedActivity?.id === activity.id ? 'ring-2 ring-blue-500 ring-offset-2' : ''
                  }`}
                >
                  <div className="p-6">
                    {/* Activity Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        {activity.is_featured && (
                          <span className="inline-flex items-center px-3 py-1 bg-yellow-100 text-yellow-700 text-sm font-medium rounded-full">
                            <Star className="w-4 h-4 mr-1" />
                            Featured
                          </span>
                        )}
                        <span className={`inline-flex items-center px-3 py-1 text-sm font-medium rounded-full ${getActivityTypeColor(activity.activity_type)}`}>
                          {getActivityTypeIcon(activity.activity_type)}
                          <span className="ml-1">{activity.activity_type.charAt(0).toUpperCase() + activity.activity_type.slice(1)}</span>
                        </span>
                        {activity.has_responded && (
                          <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 text-sm font-medium rounded-full">
                            <CheckCircle className="w-4 h-4 mr-1" />
                            Responded
                          </span>
                        )}
                      </div>
                      <span className="text-sm text-gray-500 flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {activity.time_ago}
                      </span>
                    </div>

                    {/* Activity Content */}
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">
                      {activity.title}
                    </h3>
                    <p className="text-gray-600 leading-relaxed mb-4">
                      {activity.description}
                    </p>

                    {/* Activity Stats */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span className="flex items-center">
                          <User className="w-4 h-4 mr-1" />
                          {activity.creator.full_name || activity.creator.username}
                        </span>
                        <span className="flex items-center">
                          <MessageSquare className="w-4 h-4 mr-1" />
                          {activity.response_count} responses
                        </span>
                        <span className="flex items-center">
                          <Eye className="w-4 h-4 mr-1" />
                          {activity.view_count} views
                        </span>
                      </div>
                      <span className="inline-flex items-center px-3 py-1 bg-orange-100 text-orange-700 text-sm font-medium rounded-full">
                        <Trophy className="w-4 h-4 mr-1" />
                        {activity.points_reward} pts
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Activity Detail Sidebar */}
          <div className="lg:col-span-1">
            {selectedActivity ? (
              <div className="bg-white rounded-2xl shadow-sm p-6 sticky top-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Activity Details</h3>
                  <button
                    onClick={() => setSelectedActivity(null)}
                    className="p-1 rounded-lg hover:bg-gray-100 text-gray-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {/* Activity Info */}
                <div className="space-y-4 mb-6">
                  <div>
                    <h4 className="font-medium text-gray-900">{selectedActivity.title}</h4>
                    <p className="text-sm text-gray-600 mt-1">{selectedActivity.description}</p>
                  </div>

                  {/* Activity Specifics */}
                  {selectedActivity.activity_type === 'poll' && selectedActivity.activity_data.question && (
                    <div>
                      <p className="text-sm font-medium text-gray-900 mb-2">Poll Question:</p>
                      <p className="text-sm text-gray-600">{selectedActivity.activity_data.question}</p>
                    </div>
                  )}

                  {selectedActivity.activity_type === 'quiz' && selectedActivity.activity_data.question && (
                    <div>
                      <p className="text-sm font-medium text-gray-900 mb-2">Quiz Question:</p>
                      <p className="text-sm text-gray-600">{selectedActivity.activity_data.question}</p>
                    </div>
                  )}
                </div>

                {/* Tabs */}
                <div className="flex mb-6">
                  <button
                    onClick={() => setActiveTab('respond')}
                    className={`flex-1 py-2 px-4 text-sm font-medium rounded-l-lg transition-colors ${
                      activeTab === 'respond'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <Send className="w-4 h-4 inline mr-2" />
                    Respond
                  </button>
                  <button
                    onClick={() => setActiveTab('analytics')}
                    className={`flex-1 py-2 px-4 text-sm font-medium rounded-r-lg transition-colors ${
                      activeTab === 'analytics'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    <BarChart3 className="w-4 h-4 inline mr-2" />
                    Analytics
                  </button>
                </div>

                {/* Tab Content */}
                {activeTab === 'respond' ? (
                  <>
                    {/* Response Button */}
                {!selectedActivity.has_responded || selectedActivity.allow_multiple_responses ? (
                  !showResponseForm ? (
                    <button
                      onClick={() => setShowResponseForm(true)}
                      className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200 flex items-center justify-center space-x-2"
                    >
                      <Plus className="w-4 h-4" />
                      <span>
                        {selectedActivity.has_responded ? 'Respond Again' : 'Respond'}
                      </span>
                    </button>
                  ) : (
                    <div className="space-y-4">
                      {renderResponseForm(selectedActivity)}
                      <div className="flex space-x-3">
                        <button
                          onClick={() => submitResponse(selectedActivity.id)}
                          disabled={isSubmittingResponse}
                          className="flex-1 py-3 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-blue-500/25 hover:shadow-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                        >
                          {isSubmittingResponse ? (
                            <>
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                              <span>Submitting...</span>
                            </>
                          ) : (
                            <>
                              <Send className="w-4 h-4" />
                              <span>Submit</span>
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => {
                            setShowResponseForm(false);
                            setNewResponseData({});
                          }}
                          disabled={isSubmittingResponse}
                          className="px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors disabled:opacity-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )
                ) : (
                  <div className="text-center p-4 bg-green-50 rounded-xl">
                    <CheckCircle className="w-8 h-8 text-green-600 mx-auto mb-2" />
                    <p className="text-sm text-green-700 font-medium">You've already responded!</p>
                  </div>
                )}

                    {/* Responses Section */}
                    <div className="mt-6">
                      <h4 className="font-medium text-gray-900 mb-4">Recent Responses ({responses.length})</h4>
                      <div className="space-y-3 max-h-64 overflow-y-auto">
                        {responses.length === 0 ? (
                          <p className="text-sm text-gray-500 text-center py-4">No responses yet</p>
                        ) : (
                          responses.slice(0, 5).map((response) => (
                            <div key={response.id} className="p-3 bg-gray-50 rounded-lg">
                              <div className="flex items-start justify-between mb-2">
                                <span className="text-sm font-medium text-gray-900">
                                  {response.user_name}
                                </span>
                                <span className="text-xs text-gray-500">{response.time_ago}</span>
                              </div>
                              <p className="text-sm text-gray-600">
                                {response.response_data.text_response ||
                                 response.response_data.selected_option ||
                                 response.response_data.selected_answer ||
                                 'Response shared'}
                              </p>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  /* Analytics Tab Content */
                  <div className="space-y-6">
                    {analyticsData && (
                      <>
                        {/* Analytics Header */}
                        <div className="flex items-center justify-between">
                          <h4 className="font-medium text-gray-900">Response Analytics</h4>
                          <button
                            onClick={exportResponses}
                            className="flex items-center space-x-1 px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                          >
                            <Download className="w-4 h-4" />
                            <span>Export CSV</span>
                          </button>
                        </div>

                        {/* Statistics Cards */}
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-blue-50 p-4 rounded-lg">
                            <div className="flex items-center space-x-2">
                              <Users className="w-5 h-5 text-blue-600" />
                              <div>
                                <p className="text-sm font-medium text-blue-900">Total Responses</p>
                                <p className="text-2xl font-bold text-blue-600">{analyticsData.totalResponses}</p>
                              </div>
                            </div>
                          </div>

                          <div className="bg-green-50 p-4 rounded-lg">
                            <div className="flex items-center space-x-2">
                              <Eye className="w-5 h-5 text-green-600" />
                              <div>
                                <p className="text-sm font-medium text-green-900">Response Rate</p>
                                <p className="text-2xl font-bold text-green-600">{analyticsData.responseRate}%</p>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* User Type Breakdown */}
                        <div className="bg-gray-50 p-4 rounded-lg">
                          <h5 className="font-medium text-gray-900 mb-3">User Type Breakdown</h5>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <UserCheck className="w-4 h-4 text-blue-600" />
                                <span className="text-sm text-gray-700">Registered Users</span>
                              </div>
                              <span className="text-sm font-medium text-gray-900">{analyticsData.registeredResponses}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <Mail className="w-4 h-4 text-green-600" />
                                <span className="text-sm text-gray-700">Guests</span>
                              </div>
                              <span className="text-sm font-medium text-gray-900">{analyticsData.guestResponses}</span>
                            </div>
                          </div>
                        </div>

                        {/* Response Distribution (for polls/quizzes) */}
                        {Object.keys(analyticsData.responseDistribution).length > 0 && (
                          <div className="bg-gray-50 p-4 rounded-lg">
                            <h5 className="font-medium text-gray-900 mb-3">Response Distribution</h5>
                            <div className="space-y-2">
                              {Object.entries(analyticsData.responseDistribution).map(([option, count]) => (
                                <div key={option} className="flex items-center justify-between">
                                  <span className="text-sm text-gray-700">{option}</span>
                                  <div className="flex items-center space-x-2">
                                    <div className="w-20 bg-gray-200 rounded-full h-2">
                                      <div
                                        className="bg-blue-500 h-2 rounded-full"
                                        style={{ width: `${((count as number) / analyticsData.totalResponses) * 100}%` }}
                                      ></div>
                                    </div>
                                    <span className="text-sm font-medium text-gray-900 w-8">{count}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Recent Responses */}
                        <div>
                          <h5 className="font-medium text-gray-900 mb-3">All Responses ({responses.length})</h5>
                          <div className="space-y-3 max-h-64 overflow-y-auto">
                            {responses.length === 0 ? (
                              <p className="text-sm text-gray-500 text-center py-4">No responses yet</p>
                            ) : (
                              responses.map((response) => (
                                <div key={response.id} className="p-3 bg-white border border-gray-200 rounded-lg">
                                  <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center space-x-2">
                                      <span className="text-sm font-medium text-gray-900">
                                        {response.user_name}
                                      </span>
                                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                                        response.is_guest_response
                                          ? 'bg-green-100 text-green-700'
                                          : 'bg-blue-100 text-blue-700'
                                      }`}>
                                        {response.is_guest_response ? 'Guest' : 'User'}
                                      </span>
                                    </div>
                                    <span className="text-xs text-gray-500">{response.time_ago}</span>
                                  </div>
                                  <p className="text-sm text-gray-600">
                                    {response.response_data.text ||
                                     response.response_data.selected_option ||
                                     'Response shared'}
                                  </p>
                                </div>
                              ))
                            )}
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
                <Heart className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">Select an activity to see details</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};