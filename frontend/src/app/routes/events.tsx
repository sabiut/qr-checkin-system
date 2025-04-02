import { useContext, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

interface Event {
  id: string;
  name: string;
  date: string;
  location: string;
  totalAttendees: number;
  checkedIn: number;
  capacity: number;
}

export default function EventsPage() {
  const { user, token, isAuthenticated } = useContext(AuthContext);
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setIsLoading(true);
        
        // Use token from context
        if (!token || !isAuthenticated) {
          throw new Error('Authentication required');
        }
        
        // Use the proper API URL with environment variable
        // Make sure we have a proper API URL
        let apiUrl = import.meta.env.VITE_API_URL;
        if (!apiUrl) {
          console.warn('VITE_API_URL is not defined in environment variables, falling back to http://localhost:8000');
          // If in development, try to use a fallback URL
          if (process.env.NODE_ENV === 'development') {
            apiUrl = 'http://localhost:8000';
          } else {
            throw new Error('API URL configuration is missing');
          }
        }
        
        // Make an actual API call to get events from the backend
        console.log(`Making API request to: ${apiUrl}/api/events/`);
        const response = await fetch(`${apiUrl}/api/events/`, {
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          }
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch events');
        }
        
        const eventsData = await response.json();
        
        // Process the events to get attendance counts
        const processedEvents = await Promise.all(eventsData.map(async (event: any) => {
          try {
            // For each event, we need to also get information about attendance
            const attendanceResponse = await fetch(`${apiUrl}/api/attendance/?event_id=${event.id}`, {
              headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json',
              }
            });
            const attendanceData = attendanceResponse.ok ? await attendanceResponse.json() : [];
            
            // Calculate checked-in attendees
            const checkedInCount = attendanceData.filter((record: any) => record.has_attended).length;
            
            // Get invitations count for this event (represents registered attendees)
            const invitationsResponse = await fetch(`${apiUrl}/api/invitations/?event=${event.id}`, {
              headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json',
              }
            });
            const invitationsData = invitationsResponse.ok ? await invitationsResponse.json() : [];
            
            // Return the processed event with attendance data
            return {
              id: event.id,
              name: event.name,
              date: event.date,
              location: event.location,
              totalAttendees: invitationsData.length || event.attendee_count || 0,
              checkedIn: checkedInCount || 0,
              capacity: event.max_attendees || 0
            };
          } catch (err) {
            console.error(`Error processing event ${event.id}:`, err);
            return {
              id: event.id,
              name: event.name,
              date: event.date,
              location: event.location,
              totalAttendees: event.attendee_count || 0,
              checkedIn: 0,
              capacity: event.max_attendees || 0
            };
          }
        }));
        
        setEvents(processedEvents);
        setError(null);
      } catch (err) {
        console.error('Error fetching events:', err);
        setError('Unable to load events. Please try again later.');
        
        // If the API call fails in development, fall back to sample data
        if (process.env.NODE_ENV === 'development') {
          console.log('Using sample data for development');
          setEvents([
            {
              id: '1',
              name: 'Annual Tech Conference',
              date: '2025-05-15',
              location: 'Convention Center',
              totalAttendees: 235,
              checkedIn: 210,
              capacity: 500
            },
            {
              id: '2',
              name: 'Product Launch',
              date: '2025-06-10',
              location: 'Downtown Hotel',
              totalAttendees: 86,
              checkedIn: 76,
              capacity: 150
            },
            {
              id: '3',
              name: 'Team Building Workshop',
              date: '2025-04-22',
              location: 'Office Campus',
              totalAttendees: 42,
              checkedIn: 38,
              capacity: 50
            }
          ]);
          setError(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchEvents();
  }, [token, isAuthenticated]);

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Your Events</h1>
          <Link 
            to="/events/new" 
            className="flex items-center justify-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            <span>Create New Event</span>
          </Link>
        </div>

        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        ) : events.length === 0 ? (
          <div className="bg-white rounded-xl shadow-md p-8 text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">No events yet</h2>
            <p className="text-gray-600 mb-6">Create your first event to start tracking attendance</p>
            <Link 
              to="/events/new" 
              className="inline-flex items-center justify-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
            >
              <span>Create Event</span>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((event) => (
              <Link 
                key={event.id} 
                to={`/events/${event.id}`}
                className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg transition-shadow group"
              >
                <div className="bg-gradient-to-r from-blue-600 to-indigo-700 h-3 group-hover:h-4 transition-all"></div>
                <div className="p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">{event.name}</h2>
                  <div className="flex items-center text-gray-600 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span>{new Date(event.date).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center text-gray-600 mb-6">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span>{event.location}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <div>
                      <div className="text-sm text-gray-500 mb-1">Registration</div>
                      <div className="flex items-center">
                        <span className="font-semibold">{event.totalAttendees}/{event.capacity}</span>
                        <div className="ml-2 h-2 w-20 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 rounded-full" 
                            style={{ width: `${Math.min(100, (event.totalAttendees / event.capacity) * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-500 mt-2 mb-1">Check-in Rate</div>
                      <div className="flex items-center">
                        <span className="font-semibold">{Math.round((event.checkedIn / event.totalAttendees) * 100)}%</span>
                        <div className="ml-2 h-2 w-20 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-green-500 rounded-full" 
                            style={{ width: `${Math.min(100, (event.checkedIn / event.totalAttendees) * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                    <Link to={`/events/${event.id}/check-in`} className="bg-blue-600 text-white text-sm font-medium py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                      Check-in
                    </Link>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}