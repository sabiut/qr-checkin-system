import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AlertCircle, CheckCircle, Clock, MapPin, User, Mail, Heart } from 'lucide-react';

interface ActivityData {
  question?: string;
  options?: string[];
  correct_answer?: string;
  prompt?: string;
}

interface Activity {
  id: string;
  title: string;
  description: string;
  activity_type: 'poll' | 'quiz' | 'question' | 'challenge' | 'introduction';
  activity_data: ActivityData;
  points_reward: number;
  starts_at?: string;
  ends_at?: string;
  anonymous_responses: boolean;
  event: {
    name: string;
    date: string;
    time: string;
    location: string;
  };
  creator: {
    username: string;
    first_name: string;
    last_name: string;
  };
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function GuestIcebreakerResponse() {
  const { token } = useParams();
  const navigate = useNavigate();

  const [activity, setActivity] = useState<Activity | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Form state
  const [guestName, setGuestName] = useState('');
  const [guestEmail, setGuestEmail] = useState('');
  const [response, setResponse] = useState<string | string[]>('');

  // Fetch activity data
  useEffect(() => {
    if (!token) return;

    const fetchActivity = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/communication/icebreakers/guest_response/?token=${token}`);

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || 'Failed to load activity');
        }

        const data = await response.json();
        setActivity(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load activity');
      } finally {
        setLoading(false);
      }
    };

    fetchActivity();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!activity || !guestEmail.trim()) {
      setError('Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const responseData = {
        token,
        guest_email: guestEmail.trim(),
        guest_name: guestName.trim(),
        response_data: formatResponseData()
      };

      const response = await fetch(`${API_BASE_URL}/api/communication/icebreakers/guest_response/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(responseData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to submit response');
      }

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit response');
    } finally {
      setSubmitting(false);
    }
  };

  const formatResponseData = () => {
    switch (activity?.activity_type) {
      case 'poll':
      case 'quiz':
        return { selected_option: response as string };
      case 'question':
      case 'introduction':
      case 'challenge':
        return { text: response as string };
      default:
        return { text: response as string };
    }
  };

  const renderResponseForm = () => {
    if (!activity) return null;

    switch (activity.activity_type) {
      case 'poll':
      case 'quiz':
        return (
          <div className="space-y-3">
            <label className="block text-sm font-medium text-gray-700">
              {activity.activity_data.question || 'Select your answer:'}
            </label>
            <div className="space-y-2">
              {activity.activity_data.options?.map((option, index) => (
                <label key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                  <input
                    type="radio"
                    value={option}
                    checked={response === option}
                    onChange={(e) => setResponse(e.target.value)}
                    className="w-4 h-4 text-blue-600"
                  />
                  <span className="text-gray-700">{option}</span>
                </label>
              ))}
            </div>
          </div>
        );

      case 'question':
      case 'challenge':
        return (
          <div className="space-y-3">
            <label htmlFor="response" className="block text-sm font-medium text-gray-700">
              {activity.activity_data.prompt || 'Your response:'}
            </label>
            <textarea
              id="response"
              value={response as string}
              onChange={(e) => setResponse(e.target.value)}
              placeholder="Share your thoughts..."
              rows={4}
              className="w-full px-4 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        );

      case 'introduction':
        return (
          <div className="space-y-3">
            <label htmlFor="introduction" className="block text-sm font-medium text-gray-700">
              Introduce yourself to other attendees:
            </label>
            <textarea
              id="introduction"
              value={response as string}
              onChange={(e) => setResponse(e.target.value)}
              placeholder="Tell us about yourself, your role, and what you're looking forward to at this event..."
              rows={6}
              className="w-full px-4 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        );

      default:
        return (
          <div className="space-y-3">
            <label htmlFor="response" className="block text-sm font-medium text-gray-700">
              Your response:
            </label>
            <textarea
              id="response"
              value={response as string}
              onChange={(e) => setResponse(e.target.value)}
              placeholder="Enter your response..."
              rows={4}
              className="w-full px-4 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading activity...</p>
        </div>
      </div>
    );
  }

  if (error && !activity) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Unable to Load Activity
            </h2>
            <p className="text-gray-600 mb-4">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-lg w-full bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Response Submitted!
            </h2>
            <p className="text-gray-600 mb-6">
              Thank you for participating in this icebreaker activity. Your response helps make the event more engaging for everyone!
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-800">
                <strong>Next steps:</strong> We encourage you to create an account to fully participate in event activities and earn points!
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!activity) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 mb-4">
              <Heart className="h-3 w-3 mr-1" />
              Icebreaker Activity
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {activity.title}
            </h1>
            <p className="text-gray-600">
              {activity.description}
            </p>
          </div>

          {/* Event info */}
          <div className="mb-6 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  {activity.event.name}
                </h3>
                <div className="flex items-center text-sm text-gray-600 space-x-4">
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    {activity.event.date} at {activity.event.time}
                  </div>
                  <div className="flex items-center">
                    <MapPin className="h-4 w-4 mr-1" />
                    {activity.event.location}
                  </div>
                </div>
              </div>
              {activity.points_reward > 0 && (
                <div className="text-right">
                  <div className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    🏆 {activity.points_reward} points
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    (with account)
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Response form */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">Share Your Response</h2>
              <p className="text-gray-600">
                Help break the ice and get to know fellow attendees!
              </p>
            </div>

            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
                  <p className="text-red-800">{error}</p>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Guest info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="email" className="flex items-center text-sm font-medium text-gray-700 mb-2">
                    <Mail className="h-4 w-4 mr-1" />
                    Email Address *
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={guestEmail}
                    onChange={(e) => setGuestEmail(e.target.value)}
                    placeholder="your@email.com"
                    required
                    className="w-full px-4 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-600"
                  />
                </div>
                <div>
                  <label htmlFor="name" className="flex items-center text-sm font-medium text-gray-700 mb-2">
                    <User className="h-4 w-4 mr-1" />
                    Your Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    value={guestName}
                    onChange={(e) => setGuestName(e.target.value)}
                    placeholder="Your name (optional)"
                    className="w-full px-4 py-2 text-gray-900 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-600"
                  />
                </div>
              </div>

              {/* Response form */}
              {renderResponseForm()}

              {/* Privacy note */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-sm text-gray-600">
                  <strong>Privacy:</strong> {activity.anonymous_responses
                    ? 'Your response will be shared anonymously.'
                    : 'Your response will be visible to other attendees with your name.'}
                </p>
              </div>

              {/* Submit button */}
              <button
                type="submit"
                disabled={submitting || !guestEmail.trim() || !response}
                className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                {submitting ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Submitting...
                  </span>
                ) : (
                  'Submit Response'
                )}
              </button>
            </form>

            {/* Footer */}
            <div className="mt-8 pt-6 border-t border-gray-200 text-center">
              <p className="text-sm text-gray-500">
                Created by {activity.creator.first_name} {activity.creator.last_name}
                ({activity.creator.username})
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}