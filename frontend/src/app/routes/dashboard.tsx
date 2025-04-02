import { useContext, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

interface EventStats {
  id: string;
  name: string;
  totalAttendees: number;
  checkedIn: number;
  capacity: number;
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string[];
  }[];
}

export default function Dashboard() {
  const { user, token, isAuthenticated } = useContext(AuthContext);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{
    upcomingEvents: number;
    totalAttendees: number;
    checkInRate: number;
    events: EventStats[];
  }>({ upcomingEvents: 0, totalAttendees: 0, checkInRate: 0, events: [] });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
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
        
        // Calculate total attendees and check-in rate from the processed events
        const totalAttendees = processedEvents.reduce((sum, event) => sum + event.totalAttendees, 0);
        const totalCheckedIn = processedEvents.reduce((sum, event) => sum + event.checkedIn, 0);
        const overallCheckInRate = totalAttendees > 0 ? Math.round((totalCheckedIn / totalAttendees) * 100) : 0;
        
        setStats({
          upcomingEvents: processedEvents.length,
          totalAttendees: totalAttendees,
          checkInRate: overallCheckInRate,
          events: processedEvents
        });
        
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Unable to load dashboard data. Please try again later.');
        
        // If the API call fails in development, fall back to sample data
        if (process.env.NODE_ENV === 'development') {
          console.log('Using sample data for development');
          
          // Sample data that matches the events page
          const sampleEvents = [
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
          ];
          
          const totalAttendees = sampleEvents.reduce((sum, event) => sum + event.totalAttendees, 0);
          const totalCheckedIn = sampleEvents.reduce((sum, event) => sum + event.checkedIn, 0);
          const overallCheckInRate = Math.round((totalCheckedIn / totalAttendees) * 100);
          
          setStats({
            upcomingEvents: sampleEvents.length,
            totalAttendees: totalAttendees,
            checkInRate: overallCheckInRate,
            events: sampleEvents
          });
          
          setError(null);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [token, isAuthenticated]);

  // Helper for stat cards
  const StatCard = ({ title, value, icon, color }: { title: string; value: string | number; icon: React.ReactNode; color: string }) => (
    <div className="bg-white rounded-xl shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gray-500 font-medium">{title}</h3>
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${color}`}>
          {icon}
        </div>
      </div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600">Welcome back, {user?.username || 'Event Organizer'}</p>
          </div>
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
        ) : stats.events.length === 0 ? (
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
          <>
            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <StatCard 
                title="Upcoming Events" 
                value={stats.upcomingEvents} 
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                } 
                color="bg-blue-600" 
              />
              <StatCard 
                title="Total Attendees" 
                value={stats.totalAttendees} 
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                } 
                color="bg-indigo-600" 
              />
              <StatCard 
                title="Check-in Rate" 
                value={`${stats.checkInRate}%`} 
                icon={
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                } 
                color="bg-green-600" 
              />
            </div>

            {/* Events Overview */}
            <div className="bg-white rounded-xl shadow-md p-6 mb-8">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Event Attendance Overview</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Event</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Capacity</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Registered</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Checked In</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Check-in Rate</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {stats.events.map((event) => (
                      <tr key={event.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{event.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{event.capacity}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{event.totalAttendees}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{event.checkedIn}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center">
                            <span className="text-sm text-gray-900 mr-2">
                              {event.totalAttendees ? Math.round((event.checkedIn / event.totalAttendees) * 100) : 0}%
                            </span>
                            <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-green-500 rounded-full" 
                                style={{ width: `${event.totalAttendees ? Math.round((event.checkedIn / event.totalAttendees) * 100) : 0}%` }}
                              ></div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <Link to={`/events/${event.id}`} className="text-blue-600 hover:text-blue-900">View</Link>
                          <span className="mx-2 text-gray-300">|</span>
                          <Link to={`/events/${event.id}/check-in`} className="text-green-600 hover:text-green-900">Check-in</Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-6 flex justify-center">
                <Link to="/events" className="text-blue-600 font-medium flex items-center">
                  <span>View all events</span>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-1" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </Link>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">Quick Actions</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Link 
                  to="/events/new"
                  className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-200 transition-colors flex items-center"
                >
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Create Event</h3>
                    <p className="text-sm text-gray-500">Set up a new event</p>
                  </div>
                </Link>
                <Link 
                  to="/events"
                  className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-200 transition-colors flex items-center"
                >
                  <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center mr-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Manage Events</h3>
                    <p className="text-sm text-gray-500">View and edit events</p>
                  </div>
                </Link>
                <div 
                  className="p-4 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-200 transition-colors flex items-center cursor-pointer"
                >
                  <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mr-3">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">Export Reports</h3>
                    <p className="text-sm text-gray-500">Download attendance data</p>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}