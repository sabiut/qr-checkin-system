import { useState, useEffect, useContext } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Calendar, Clock, MapPin, Users, QrCode, Mail, Phone, AlertCircle, 
         PlusCircle, XCircle, ChevronLeft, Check, Loader2, UserCheck, ClipboardList,
         Trash2, X } from 'lucide-react';
import { AuthContext } from '../context/AuthContext';

interface Event {
  id: number;
  name: string;
  description: string;
  date: string;
  time: string;
  location: string;
  attendee_count: number;
  max_attendees: number | null;
  is_full: boolean;
}

interface Invitation {
  id: string;
  guest_name: string;
  guest_email: string;
  guest_phone: string;
  qr_code_url: string;
  created_at: string;
}

export default function EventDetail() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const { token, isAuthenticated } = useContext(AuthContext);
  
  const [event, setEvent] = useState<Event | null>(null);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(typeof navigator !== 'undefined' ? !navigator.onLine : false);
  
  // Redirect if not authenticated for protected operations
  useEffect(() => {
    // Note: We won't redirect immediately since viewing the event can be public,
    // but we'll restrict actions based on authentication status in the UI
  }, [isAuthenticated]);
  
  // Form state for new invitation
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [formData, setFormData] = useState({
    guest_name: '',
    guest_email: '',
    guest_phone: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [inviteSuccess, setInviteSuccess] = useState(false);

  // Formatted date for display
  const formattedDate = event?.date ? new Date(event.date).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  }) : '';

  // Check online status
  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // State for attendees
  const [attendees, setAttendees] = useState<any[]>([]);
  const [showAttendeesList, setShowAttendeesList] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load event data
  useEffect(() => {
    const fetchEvent = async () => {
      if (!eventId) return;
      
      try {
        setLoading(true);
        
        // Try to get from local storage first (for offline mode)
        if (typeof window !== 'undefined' && window.localStorage) {
          const cachedEvents = localStorage.getItem('events');
          
          if (cachedEvents) {
            const parsedEvents = JSON.parse(cachedEvents);
            const foundEvent = parsedEvents.find((e: Event) => e.id.toString() === eventId);
            
            if (foundEvent) {
              setEvent(foundEvent);
            }
          }
          
          // Try to get cached invitations
          const cachedInvitations = localStorage.getItem(`invitations_${eventId}`);
          if (cachedInvitations) {
            setInvitations(JSON.parse(cachedInvitations));
          }

          // Try to get cached attendees
          const cachedAttendees = localStorage.getItem(`attendees_${eventId}`);
          if (cachedAttendees) {
            setAttendees(JSON.parse(cachedAttendees));
          }
        }
        
        // Otherwise fetch from API if online
        if (!isOffline) {
          // Prepare headers with authentication token
          const headers: HeadersInit = {
            'Content-Type': 'application/json',
          };
          
          // Add authentication token if available
          if (token) {
            headers['Authorization'] = `Token ${token}`;
          }
          
          const eventPromise = fetch(`${import.meta.env.VITE_API_URL}/api/events/${eventId}/`, {
            headers
          })
            .then(res => {
              if (!res.ok) throw new Error('Failed to fetch event');
              return res.json();
            })
            .then(data => {
              setEvent(data);
              
              // Update the cached events
              if (typeof window !== 'undefined' && window.localStorage && cachedEvents) {
                const parsedEvents = JSON.parse(cachedEvents);
                const updatedEvents = parsedEvents.map((e: Event) => 
                  e.id.toString() === eventId ? data : e
                );
                localStorage.setItem('events', JSON.stringify(updatedEvents));
              }
            });
          
          const invitationsPromise = fetch(`${import.meta.env.VITE_API_URL}/api/invitations/?event_id=${eventId}`, {
            headers
          })
            .then(res => {
              if (!res.ok) throw new Error('Failed to fetch invitations');
              return res.json();
            })
            .then(data => {
              setInvitations(data);
              if (typeof window !== 'undefined' && window.localStorage) {
                localStorage.setItem(`invitations_${eventId}`, JSON.stringify(data));
              }
            });
          
          // Fetch attendees
          const attendeesPromise = fetch(`${import.meta.env.VITE_API_URL}/api/attendance/?event_id=${eventId}`, {
            headers
          })
            .then(res => {
              if (!res.ok) throw new Error('Failed to fetch attendees');
              return res.json();
            })
            .then(data => {
              // Filter to only include those who have actually checked in
              const checkedInAttendees = data.filter((a: any) => a.has_attended);
              setAttendees(checkedInAttendees);
              if (typeof window !== 'undefined' && window.localStorage) {
                localStorage.setItem(`attendees_${eventId}`, JSON.stringify(checkedInAttendees));
              }
            });
          
          await Promise.all([eventPromise, invitationsPromise, attendeesPromise]);
        }
      } catch (err) {
        setError('Could not load event information');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvent();
  }, [eventId, isOffline]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!eventId) return;
    
    try {
      setIsSubmitting(true);
      setFormError(null);
      
      // Handle offline mode
      if (isOffline && typeof window !== 'undefined' && window.localStorage) {
        // Create a temporary invitation
        const tempInvitation: Invitation = {
          id: `temp_${Date.now()}`,
          guest_name: formData.guest_name,
          guest_email: formData.guest_email,
          guest_phone: formData.guest_phone,
          qr_code_url: '',
          created_at: new Date().toISOString(),
        };
        
        // Store in pending invitations
        const pendingInvitations = JSON.parse(localStorage.getItem('pending_invitations') || '[]');
        pendingInvitations.push({
          ...tempInvitation,
          event_id: eventId
        });
        localStorage.setItem('pending_invitations', JSON.stringify(pendingInvitations));
        
        // Update local invitations
        const updatedInvitations = [...invitations, tempInvitation];
        setInvitations(updatedInvitations);
        localStorage.setItem(`invitations_${eventId}`, JSON.stringify(updatedInvitations));
        
        // Reset form and show success message
        setFormData({ guest_name: '', guest_email: '', guest_phone: '' });
        setInviteSuccess(true);
        setTimeout(() => {
          setInviteSuccess(false);
          setShowInviteForm(false);
        }, 2000);
        return;
      }
      
      // Online mode - submit to API
      console.log('Creating invitation:', formData);
      
      // Prepare headers with authentication token
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
      
      // Add authentication token if available
      if (token) {
        headers['Authorization'] = `Token ${token}`;
      }
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/invitations/`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          ...formData,
          event: eventId,
        }),
      });
      
      // Check if we received HTML instead of JSON
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('text/html')) {
        throw new Error('Server returned an HTML error page. Please check your network connection.');
      }
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create invitation');
      }
      
      const newInvitation = await response.json();
      
      // Update local invitations
      const updatedInvitations = [...invitations, newInvitation];
      setInvitations(updatedInvitations);
      localStorage.setItem(`invitations_${eventId}`, JSON.stringify(updatedInvitations));
      
      // Reset form and show success message
      setFormData({ guest_name: '', guest_email: '', guest_phone: '' });
      setInviteSuccess(true);
      setTimeout(() => {
        setInviteSuccess(false);
        setShowInviteForm(false);
      }, 2000);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'An error occurred creating the invitation');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Function to determine status badge color
  const getAttendeeStatusBadge = () => {
    if (!event) return null;
    
    if (event.is_full) {
      return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">Full</span>;
    }
    
    if (event.max_attendees && event.attendee_count >= event.max_attendees * 0.8) {
      return <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">Almost Full</span>;
    }
    
    return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">Open</span>;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 size={40} className="animate-spin mx-auto text-blue-600 mb-4" />
          <p className="text-gray-600">Loading event information...</p>
        </div>
      </div>
    );
  }

  if (error && !event) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center text-red-500 mb-2">
              <AlertCircle size={24} className="mr-2" />
              <h2 className="text-xl font-semibold">Error</h2>
            </div>
            <p className="text-gray-600">{error}</p>
          </div>
          <div className="bg-gray-50 p-4">
            <button 
              onClick={() => navigate(-1)}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded bg-gray-800 text-white hover:bg-gray-900 transition-colors"
            >
              <ChevronLeft size={18} />
              <span>Go Back</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center p-6 bg-white rounded-lg shadow-md">
          <AlertCircle size={40} className="mx-auto text-gray-400 mb-3" />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Event Not Found</h2>
          <p className="text-gray-600 mb-4">The event you're looking for doesn't exist or may have been removed.</p>
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <ChevronLeft size={18} />
            <span>Back to Events</span>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with navigation */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <Link to="/" className="text-gray-600 hover:text-gray-900 p-2 rounded-full hover:bg-gray-100 mr-2">
                <ChevronLeft size={20} />
              </Link>
              <h1 className="text-xl font-bold text-gray-900 truncate">
                {event.name}
              </h1>
            </div>
            {isOffline && (
              <div className="flex items-center px-3 py-1 bg-yellow-50 text-yellow-800 rounded-full text-sm">
                <AlertCircle size={16} className="mr-1" />
                <span>Offline Mode</span>
              </div>
            )}
          </div>
        </div>
      </header>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              {/* Event Banner */}
              <div className="h-48 bg-gradient-to-r from-blue-500 to-indigo-600 flex items-center justify-center">
                <div className="text-center px-6">
                  <h1 className="text-3xl font-bold text-white mb-2">{event.name}</h1>
                  <div className="flex flex-wrap justify-center gap-2 mt-4">
                    {getAttendeeStatusBadge()}
                    <span className="px-2 py-1 text-xs font-medium bg-white/20 text-white rounded-full backdrop-blur-sm">
                      {event.attendee_count} {event.attendee_count === 1 ? 'Attendee' : 'Attendees'}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Event Details */}
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div className="flex items-start">
                    <div className="flex-shrink-0 bg-blue-100 p-3 rounded-lg">
                      <Calendar size={24} className="text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-sm font-medium text-gray-500">Date</h3>
                      <p className="mt-1 text-base font-medium text-gray-900">{formattedDate}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="flex-shrink-0 bg-purple-100 p-3 rounded-lg">
                      <Clock size={24} className="text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-sm font-medium text-gray-500">Time</h3>
                      <p className="mt-1 text-base font-medium text-gray-900">{event.time}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="flex-shrink-0 bg-green-100 p-3 rounded-lg">
                      <MapPin size={24} className="text-green-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-sm font-medium text-gray-500">Location</h3>
                      <p className="mt-1 text-base font-medium text-gray-900">{event.location}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="flex-shrink-0 bg-orange-100 p-3 rounded-lg">
                      <Users size={24} className="text-orange-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-sm font-medium text-gray-500">Capacity</h3>
                      <p className="mt-1 text-base font-medium text-gray-900">
                        {event.attendee_count} / {event.max_attendees || 'Unlimited'}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="mt-8">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">About this event</h2>
                  <div className="prose prose-blue max-w-none text-gray-700">
                    {event.description ? (
                      <p>{event.description}</p>
                    ) : (
                      <p className="text-gray-500 italic">No description available.</p>
                    )}
                  </div>
                </div>
                
                <div className="mt-8 pt-6 border-t flex flex-wrap gap-3">
                  <Link
                    to="/"
                    className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                  >
                    <ChevronLeft size={18} />
                    <span>All Events</span>
                  </Link>
                  
                  <Link
                    to={`/events/${event.id}/check-in`}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition-colors"
                  >
                    <UserCheck size={18} />
                    <span>Check-in Guests</span>
                  </Link>

                  <button
                    onClick={() => setShowAttendeesList(!showAttendeesList)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                  >
                    <ClipboardList size={18} />
                    <span>{showAttendeesList ? 'Hide Attendees' : 'View Attendees'}</span>
                  </button>

                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors"
                  >
                    <Trash2 size={18} />
                    <span>Delete Event</span>
                  </button>
                </div>

                {showAttendeesList && (
                  <div className="mt-6 border-t pt-6">
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-xl font-semibold text-gray-900">Attendees List</h2>
                      <div className="flex items-center justify-center h-7 min-w-7 px-2 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                        {attendees.length}
                      </div>
                    </div>
                    
                    {attendees.length === 0 ? (
                      <div className="text-center py-8 bg-gray-50 rounded-lg">
                        <Users size={40} className="mx-auto text-gray-300 mb-3" />
                        <p className="text-gray-500">No attendees yet</p>
                        <p className="text-sm text-gray-400 mt-1">Attendees will appear here after check-in.</p>
                      </div>
                    ) : (
                      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                          <thead className="bg-gray-50">
                            <tr>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Guest Name
                              </th>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Contact Info
                              </th>
                              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Check-in Time
                              </th>
                            </tr>
                          </thead>
                          <tbody className="bg-white divide-y divide-gray-200">
                            {attendees.map((attendee) => (
                              <tr key={attendee.id}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <div className="text-sm font-medium text-gray-900">
                                    {attendee.invitation_details.guest_name}
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                  <div className="text-sm text-gray-500">
                                    {attendee.invitation_details.guest_email && (
                                      <div className="flex items-center">
                                        <Mail size={14} className="mr-1 text-gray-400" />
                                        <span>{attendee.invitation_details.guest_email}</span>
                                      </div>
                                    )}
                                    {attendee.invitation_details.guest_phone && (
                                      <div className="flex items-center mt-1">
                                        <Phone size={14} className="mr-1 text-gray-400" />
                                        <span>{attendee.invitation_details.guest_phone}</span>
                                      </div>
                                    )}
                                  </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                  {attendee.check_in_time ? new Date(attendee.check_in_time).toLocaleString() : 'N/A'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex justify-between items-center mb-5">
                <h2 className="text-xl font-semibold text-gray-900">Invitations</h2>
                <div className="flex items-center justify-center h-7 min-w-7 px-2 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                  {invitations.length}
                </div>
              </div>
              
              {inviteSuccess && (
                <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-lg flex items-center">
                  <Check size={18} className="mr-2 flex-shrink-0" />
                  <span>Invitation created successfully!</span>
                </div>
              )}
              
              {showInviteForm ? (
                <div className="mb-5">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="font-medium text-gray-900">New Invitation</h3>
                    <button
                      onClick={() => {
                        setShowInviteForm(false);
                        setFormError(null);
                      }}
                      className="text-gray-400 hover:text-gray-600"
                      aria-label="Close form"
                    >
                      <XCircle size={20} />
                    </button>
                  </div>
                  
                  {formError && (
                    <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg flex items-start">
                      <AlertCircle size={16} className="mr-2 mt-0.5 flex-shrink-0" />
                      <span>{formError}</span>
                    </div>
                  )}
                  
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <label htmlFor="guest_name" className="block text-sm font-medium text-gray-700 mb-1">
                        Guest Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        id="guest_name"
                        name="guest_name"
                        value={formData.guest_name}
                        onChange={handleChange}
                        required
                        placeholder="Enter guest name"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 focus:outline-none text-gray-900"
                      />
                    </div>
                    
                    <div>
                      <label htmlFor="guest_email" className="block text-sm font-medium text-gray-700 mb-1">
                        Email
                      </label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <Mail size={16} className="text-gray-400" />
                        </div>
                        <input
                          type="email"
                          id="guest_email"
                          name="guest_email"
                          value={formData.guest_email}
                          onChange={handleChange}
                          placeholder="guest@example.com"
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 focus:outline-none text-gray-900"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label htmlFor="guest_phone" className="block text-sm font-medium text-gray-700 mb-1">
                        Phone
                      </label>
                      <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                          <Phone size={16} className="text-gray-400" />
                        </div>
                        <input
                          type="tel"
                          id="guest_phone"
                          name="guest_phone"
                          value={formData.guest_phone}
                          onChange={handleChange}
                          placeholder="(123) 456-7890"
                          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 focus:outline-none text-gray-900"
                        />
                      </div>
                    </div>
                    
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-400 transition-colors"
                    >
                      {isSubmitting ? (
                        <>
                          <Loader2 size={18} className="animate-spin" />
                          <span>Creating...</span>
                        </>
                      ) : (
                        <>
                          <Check size={18} />
                          <span>Create Invitation</span>
                        </>
                      )}
                    </button>
                  </form>
                </div>
              ) : (
                <button
                  onClick={() => setShowInviteForm(true)}
                  className="w-full mb-5 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                >
                  <PlusCircle size={18} />
                  <span>Create Invitation</span>
                </button>
              )}
              
              <div className="overflow-y-auto max-h-96 pr-1">
                {invitations.length === 0 ? (
                  <div className="text-center py-8">
                    <Users size={40} className="mx-auto text-gray-300 mb-3" />
                    <p className="text-gray-500">No invitations yet</p>
                    <p className="text-sm text-gray-400 mt-1">Create an invitation to get started.</p>
                  </div>
                ) : (
                  <ul className="space-y-3">
                    {invitations.map(invitation => (
                      <li 
                        key={invitation.id} 
                        className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-colors"
                      >
                        <div className="font-medium text-gray-900">{invitation.guest_name}</div>
                        <div className="mt-2 flex flex-col gap-1 text-sm">
                          {invitation.guest_email && (
                            <div className="flex items-center text-gray-600">
                              <Mail size={14} className="mr-1.5 text-gray-400" />
                              <span>{invitation.guest_email}</span>
                            </div>
                          )}
                          {invitation.guest_phone && (
                            <div className="flex items-center text-gray-600">
                              <Phone size={14} className="mr-1.5 text-gray-400" />
                              <span>{invitation.guest_phone}</span>
                            </div>
                          )}
                        </div>
                        {invitation.qr_code_url ? (
                          <div className="mt-3">
                            <a 
                              href={`${import.meta.env.VITE_API_URL}${invitation.qr_code_url}`} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="flex items-center gap-1.5 text-blue-600 text-sm hover:text-blue-800"
                            >
                              <QrCode size={16} />
                              <span>View QR Code</span>
                            </a>
                            {invitation.guest_email && (
                              <button 
                                onClick={async () => {
                                  try {
                                    // Prepare headers with authentication token
                                    const headers: HeadersInit = {
                                      'Content-Type': 'application/json',
                                    };
                                    
                                    // Add authentication token if available
                                    if (token) {
                                      headers['Authorization'] = `Token ${token}`;
                                    }
                                    
                                    const response = await fetch(
                                      `${import.meta.env.VITE_API_URL}/api/invitations/${invitation.id}/send_email/`,
                                      {
                                        method: 'POST',
                                        headers
                                      }
                                    );
                                    if (response.ok) {
                                      alert(`Invitation email sent to ${invitation.guest_email}`);
                                    } else {
                                      const error = await response.json();
                                      throw new Error(error.error || 'Failed to send email');
                                    }
                                  } catch (err) {
                                    console.error('Error sending email:', err);
                                    alert(`Error sending email: ${err instanceof Error ? err.message : String(err)}`);
                                  }
                                }}
                                className="flex items-center gap-1.5 text-purple-600 text-sm hover:text-purple-800 mt-2"
                              >
                                <Mail size={16} />
                                <span>Send QR by Email</span>
                              </button>
                            )}
                          </div>
                        ) : (
                          <div className="mt-3 flex items-center gap-1.5 text-yellow-600 text-sm italic">
                            <AlertCircle size={16} className="text-yellow-500" />
                            <span>QR code will be available when online</span>
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-lg">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-900">Delete Event</h3>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={24} />
              </button>
            </div>
            
            <div className="py-4">
              <div className="flex items-center text-red-600 mb-4">
                <AlertCircle size={24} className="mr-2" />
                <p className="font-medium">This action cannot be undone</p>
              </div>
              <p className="text-gray-700 mb-2">
                Are you sure you want to delete this event?
              </p>
              <p className="text-gray-600 text-sm">
                <strong>{event.name}</strong>
              </p>
              <p className="text-gray-600 text-sm">
                {new Date(event.date).toLocaleDateString()} at {event.time}
              </p>
            </div>
            
            <div className="flex justify-end gap-3 mt-4 pt-4 border-t">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (!token || !eventId) return;
                  
                  try {
                    setIsDeleting(true);
                    
                    // Prepare headers with authentication token
                    const headers: HeadersInit = {
                      'Content-Type': 'application/json',
                    };
                    
                    if (token) {
                      headers['Authorization'] = `Token ${token}`;
                    }
                    
                    // Send delete request
                    const response = await fetch(`${import.meta.env.VITE_API_URL}/api/events/${eventId}/`, {
                      method: 'DELETE',
                      headers
                    });
                    
                    if (!response.ok) {
                      throw new Error(`Error: ${response.status}`);
                    }
                    
                    // Delete successful, redirect to home page
                    navigate('/', { replace: true });
                  } catch (error) {
                    console.error('Error deleting event:', error);
                    alert('Failed to delete event. Please try again later.');
                    setShowDeleteConfirm(false);
                    setIsDeleting(false);
                  }
                }}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-red-400 flex items-center"
              >
                {isDeleting ? (
                  <>
                    <Loader2 size={18} className="animate-spin mr-2" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 size={18} className="mr-2" />
                    <span>Delete Event</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}