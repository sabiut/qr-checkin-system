import { useState, useEffect, useContext } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Calendar, Clock, MapPin, Users, AlertCircle, X, ChevronLeft, Save, Video, Monitor, Globe } from 'lucide-react';
import { AuthContext } from '../context/AuthContext';

export default function NewEvent() {
  const navigate = useNavigate();
  const { token, isAuthenticated } = useContext(AuthContext);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [isBrowser, setIsBrowser] = useState(false);
  
  // Redirect if not authenticated
  useEffect(() => {
    if (isBrowser && !isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [isAuthenticated, navigate, isBrowser]);
  
  // Initialize form data with empty strings
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    date: '',
    time: '',
    location: '',
    max_attendees: '',
    event_type: 'in_person',
    virtual_link: '',
    virtual_meeting_id: '',
    virtual_passcode: '',
    virtual_platform: '',
  });

  // Separate references for date and time inputs to avoid React controlled component issues
  const [dateInputKey, setDateInputKey] = useState('date-input-' + Date.now());
  const [timeInputKey, setTimeInputKey] = useState('time-input-' + Date.now());
  
  // Check if we're in browser
  useEffect(() => {
    setIsBrowser(true);
    if (typeof navigator !== 'undefined') {
      setIsOffline(!navigator.onLine);
    }
  }, []);
  
  // Check online status
  useEffect(() => {
    if (!isBrowser) return;
    
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [isBrowser]);

  // Handle changes for text and number inputs
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Special handler for date input to ensure proper format
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    setFormData(prev => ({ ...prev, date: value }));
  };

  // Special handler for time input to ensure proper format
  const handleTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    setFormData(prev => ({ ...prev, time: value }));
  };

  // Safe JSON parsing function
  const safeParseJSON = async (response: Response) => {
    const text = await response.text();
    
    try {
      // Try to parse as JSON
      return JSON.parse(text);
    } catch (e) {
      // If it's not valid JSON, check if it's HTML
      if (text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html')) {
        // This is an HTML response, likely an error page
        console.error('Received HTML instead of JSON:', text.substring(0, 150) + '...');
        throw new Error(`Server returned an HTML page instead of JSON. Status: ${response.status} ${response.statusText}`);
      }
      
      // Otherwise, return the raw text
      return { error: text };
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setIsSubmitting(true);
      setError(null);
      
      // Handle offline mode
      if (isOffline && typeof window !== 'undefined') {
        // Store in pending events
        const pendingEvents = JSON.parse(localStorage.getItem('pending_events') || '[]');
        
        // Create a temporary ID for client-side reference
        const tempEvent = {
          ...formData,
          id: `temp_${Date.now()}`,
          attendee_count: 0,
          is_full: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          max_attendees: formData.max_attendees ? parseInt(formData.max_attendees) : null,
        };
        
        pendingEvents.push(tempEvent);
        localStorage.setItem('pending_events', JSON.stringify(pendingEvents));
        
        // Also add to events cache for immediate display
        const cachedEvents = JSON.parse(localStorage.getItem('events') || '[]');
        cachedEvents.push(tempEvent);
        localStorage.setItem('events', JSON.stringify(cachedEvents));
        
        // Navigate back
        navigate('/');
        return;
      }
      
      // Log the API URL for debugging
      console.log('Using API URL:', import.meta.env.VITE_API_URL);
      
      // Online mode - submit to API
      const apiUrl = `${import.meta.env.VITE_API_URL}/api/events/`;
      console.log('Submitting to:', apiUrl);
      
      // Prepare headers with authentication token
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
      
      // Add authentication token if available
      if (token) {
        headers['Authorization'] = `Token ${token}`;
      }
      
      // Clean the form data - remove empty virtual event fields for in-person events
      const cleanedData = {
        ...formData,
        max_attendees: formData.max_attendees ? parseInt(formData.max_attendees) : null,
      };
      
      // For in-person events, remove virtual event fields to avoid validation errors
      if (formData.event_type === 'in_person') {
        delete cleanedData.virtual_link;
        delete cleanedData.virtual_meeting_id;
        delete cleanedData.virtual_passcode;
        delete cleanedData.virtual_platform;
      } else {
        // For virtual/hybrid events, only send virtual fields if they have values
        if (!formData.virtual_link || formData.virtual_link.trim() === '') {
          delete cleanedData.virtual_link;
        }
        if (!formData.virtual_meeting_id || formData.virtual_meeting_id.trim() === '') {
          delete cleanedData.virtual_meeting_id;
        }
        if (!formData.virtual_passcode || formData.virtual_passcode.trim() === '') {
          delete cleanedData.virtual_passcode;
        }
        if (!formData.virtual_platform || formData.virtual_platform.trim() === '') {
          delete cleanedData.virtual_platform;
        }
      }

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(cleanedData),
      });
      
      // Log the response status for debugging
      console.log('Response status:', response.status, response.statusText);
      
      // Check response content type to detect HTML response
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('text/html')) {
        throw new Error(`Server returned HTML (${response.status}). Check the API URL and server configuration.`);
      }
      
      if (!response.ok) {
        // Safely parse the response, which might not be JSON
        const data = await safeParseJSON(response);
        const errorMessage = data.detail || `Error ${response.status}: ${response.statusText}`;
        throw new Error(errorMessage);
      }
      
      // Safely parse the successful response
      const newEvent = await safeParseJSON(response);
      
      // Check if the response contains the expected data
      if (!newEvent || !newEvent.id) {
        throw new Error('Invalid response format from server');
      }
      
      // Update the cached events
      if (typeof window !== 'undefined' && window.localStorage) {
        const cachedEvents = localStorage.getItem('events');
        if (cachedEvents) {
          const parsedEvents = JSON.parse(cachedEvents);
          parsedEvents.push(newEvent);
          localStorage.setItem('events', JSON.stringify(parsedEvents));
        }
      }
      
      // Navigate to the new event
      navigate(`/events/${newEvent.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred creating the event');
      console.error('Submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Don't render anything during SSR
  if (!isBrowser) {
    return null;
  }

  // Get today's date in YYYY-MM-DD format for the min attribute
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="p-2 -ml-2 text-gray-600 hover:text-gray-900 rounded-full hover:bg-gray-100">
              <ChevronLeft size={20} />
            </Link>
            <h1 className="text-2xl font-bold text-gray-800">Create New Event</h1>
          </div>
        </div>
      </div>
      
      <div className="max-w-3xl mx-auto px-4 py-8">
        {isOffline && (
          <div className="mb-6 p-4 bg-yellow-50 text-yellow-800 rounded-lg border border-yellow-200 flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <AlertCircle size={18} />
            </div>
            <div>
              <h3 className="font-medium">Offline Mode</h3>
              <p className="text-sm mt-1">
                You are currently offline. The event will be saved locally and synced when you're back online.
              </p>
            </div>
          </div>
        )}
        
        {error && (
          <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 flex items-start gap-3">
            <div className="flex-shrink-0 mt-0.5">
              <AlertCircle size={18} />
            </div>
            <div>
              <h3 className="font-medium">Error</h3>
              <p className="text-sm mt-1">{error}</p>
            </div>
          </div>
        )}
        
        <div className="bg-white rounded-xl shadow-sm p-6 md:p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="name" className="flex items-center text-sm font-medium text-gray-700 mb-1.5">
                <span>Event Name</span>
                <span className="ml-1 text-red-500">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                placeholder="Enter event name"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
              />
            </div>
            
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1.5">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={4}
                placeholder="Describe your event"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
              />
              <p className="mt-1.5 text-xs text-gray-500">Provide details about your event to help attendees understand what to expect.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="date" className="flex items-center text-sm font-medium text-gray-700 mb-1.5">
                  <Calendar size={16} className="mr-1.5 text-gray-500" />
                  <span>Date</span>
                  <span className="ml-1 text-red-500">*</span>
                </label>
                <div className="flex items-center">
                  <div className="bg-gray-100 p-2.5 rounded-l-lg border border-r-0 border-gray-300">
                    <Calendar size={18} className="text-blue-500" />
                  </div>
                  {/* Using a key to force re-render and avoid Chrome issues with controlled inputs */}
                  <input
                    key={dateInputKey}
                    type="date"
                    id="date"
                    name="date"
                    defaultValue={formData.date}
                    onChange={handleDateChange}
                    required
                    min={today}
                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-r-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
                    style={{ 
                      appearance: 'textfield', // Override Chrome's default styles
                      WebkitAppearance: 'none' // Try to force Chrome to show the date picker
                    }}
                    onClick={(e) => {
                      // Force Chrome to show the date picker when clicked
                      const target = e.target as HTMLInputElement;
                      target.showPicker && target.showPicker();
                    }}
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">Select a date for your event (today or later)</p>
              </div>
              
              <div>
                <label htmlFor="time" className="flex items-center text-sm font-medium text-gray-700 mb-1.5">
                  <Clock size={16} className="mr-1.5 text-gray-500" />
                  <span>Time</span>
                  <span className="ml-1 text-red-500">*</span>
                </label>
                <div className="flex items-center">
                  <div className="bg-gray-100 p-2.5 rounded-l-lg border border-r-0 border-gray-300">
                    <Clock size={18} className="text-blue-500" />
                  </div>
                  {/* Using a key to force re-render and avoid Chrome issues with controlled inputs */}
                  <input
                    key={timeInputKey}
                    type="time"
                    id="time"
                    name="time"
                    defaultValue={formData.time}
                    onChange={handleTimeChange}
                    required
                    className="flex-1 px-4 py-2.5 border border-gray-300 rounded-r-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
                    style={{ 
                      appearance: 'textfield', // Override Chrome's default styles
                      WebkitAppearance: 'none' // Try to force Chrome to show the time picker
                    }}
                    onClick={(e) => {
                      // Force Chrome to show the time picker when clicked
                      const target = e.target as HTMLInputElement;
                      target.showPicker && target.showPicker();
                    }}
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">Choose the start time of your event</p>
              </div>
            </div>
            
            <div>
              <label htmlFor="location" className="flex items-center text-sm font-medium text-gray-700 mb-1.5">
                <MapPin size={16} className="mr-1.5 text-gray-500" />
                <span>Location</span>
                <span className="ml-1 text-red-500">*</span>
              </label>
              <input
                type="text"
                id="location"
                name="location"
                value={formData.location}
                onChange={handleChange}
                required
                placeholder="Enter venue or address"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
              />
            </div>

            {/* Event Type Selection */}
            <div>
              <label htmlFor="event_type" className="flex items-center text-sm font-medium text-gray-700 mb-1.5">
                <Monitor size={16} className="mr-1.5 text-gray-500" />
                <span>Event Type</span>
                <span className="ml-1 text-red-500">*</span>
              </label>
              <select
                id="event_type"
                name="event_type"
                value={formData.event_type}
                onChange={handleChange}
                required
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900 bg-white"
              >
                <option value="in_person">In-Person</option>
                <option value="virtual">Virtual</option>
                <option value="hybrid">Hybrid (In-Person + Virtual)</option>
              </select>
              <p className="mt-1.5 text-xs text-gray-500">Choose whether this is an in-person, virtual, or hybrid event.</p>
            </div>

            {/* Virtual Event Fields - Show when event is virtual or hybrid */}
            {(formData.event_type === 'virtual' || formData.event_type === 'hybrid') && (
              <div className="space-y-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center mb-4">
                  <Video size={20} className="text-blue-600 mr-2" />
                  <h3 className="text-lg font-semibold text-blue-900">Virtual Event Details</h3>
                </div>

                <div>
                  <label htmlFor="virtual_platform" className="flex items-center text-sm font-medium text-gray-700 mb-1.5">
                    <Globe size={16} className="mr-1.5 text-gray-500" />
                    <span>Platform</span>
                    <span className="ml-1 text-red-500">*</span>
                  </label>
                  <select
                    id="virtual_platform"
                    name="virtual_platform"
                    value={formData.virtual_platform}
                    onChange={handleChange}
                    required={formData.event_type === 'virtual' || formData.event_type === 'hybrid'}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900 bg-white"
                  >
                    <option value="">Select platform</option>
                    <option value="zoom">Zoom</option>
                    <option value="teams">Microsoft Teams</option>
                    <option value="meet">Google Meet</option>
                    <option value="webex">Cisco Webex</option>
                    <option value="gotomeeting">GoToMeeting</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="virtual_link" className="flex items-center text-sm font-medium text-gray-700 mb-1.5">
                    <Globe size={16} className="mr-1.5 text-gray-500" />
                    <span>Meeting Link</span>
                    <span className="ml-1 text-red-500">*</span>
                  </label>
                  <input
                    type="url"
                    id="virtual_link"
                    name="virtual_link"
                    value={formData.virtual_link}
                    onChange={handleChange}
                    required={formData.event_type === 'virtual' || formData.event_type === 'hybrid'}
                    placeholder="https://zoom.us/j/123456789 or https://teams.microsoft.com/..."
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
                  />
                  <p className="mt-1.5 text-xs text-gray-500">Full URL that attendees will use to join the virtual event.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="virtual_meeting_id" className="block text-sm font-medium text-gray-700 mb-1.5">
                      Meeting ID
                      <span className="ml-1 text-gray-400 text-xs">(optional)</span>
                    </label>
                    <input
                      type="text"
                      id="virtual_meeting_id"
                      name="virtual_meeting_id"
                      value={formData.virtual_meeting_id}
                      onChange={handleChange}
                      placeholder="123-456-789"
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
                    />
                  </div>

                  <div>
                    <label htmlFor="virtual_passcode" className="block text-sm font-medium text-gray-700 mb-1.5">
                      Passcode
                      <span className="ml-1 text-gray-400 text-xs">(optional)</span>
                    </label>
                    <input
                      type="text"
                      id="virtual_passcode"
                      name="virtual_passcode"
                      value={formData.virtual_passcode}
                      onChange={handleChange}
                      placeholder="Meeting passcode"
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
                    />
                  </div>
                </div>

                <p className="text-xs text-blue-700 bg-blue-100 p-3 rounded-lg">
                  <strong>Note:</strong> Virtual event details will be included in tickets and shown to attendees. Make sure all information is accurate before creating the event.
                </p>
              </div>
            )}
            
            <div>
              <label htmlFor="max_attendees" className="flex items-center text-sm font-medium text-gray-700 mb-1.5">
                <Users size={16} className="mr-1.5 text-gray-500" />
                <span>Maximum Attendees</span>
                <span className="ml-1 text-gray-400 text-xs">(optional)</span>
              </label>
              <input
                type="number"
                id="max_attendees"
                name="max_attendees"
                value={formData.max_attendees}
                onChange={handleChange}
                min="0"
                placeholder="Leave blank for unlimited"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/20 focus:outline-none focus:border-blue-500 transition-colors text-gray-900"
              />
              <p className="mt-1.5 text-xs text-gray-500">Set a capacity limit or leave blank for unlimited attendees.</p>
            </div>
            
            <div className="flex flex-col-reverse sm:flex-row justify-between gap-3 pt-4 border-t">
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
              >
                <X size={18} />
                <span>Cancel</span>
              </button>
              
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 transition-colors font-medium"
              >
                {isSubmitting ? (
                  <>
                    <div className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></div>
                    <span>Creating...</span>
                  </>
                ) : (
                  <>
                    <Save size={18} />
                    <span>Create Event</span>
                  </>
                )}
              </button>
            </div>
            
          </form>
        </div>
        
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>
            Fields marked with <span className="text-red-500">*</span> are required.
          </p>
        </div>
      </div>
    </div>
  );
}