import { useState, useEffect, useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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

interface FeatureProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}

export default function Home() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const { isAuthenticated, user, token } = useContext(AuthContext);
  const navigate = useNavigate();
  
  // Used to control displaying marketing content only to non-authenticated users
  const showMarketingContent = !isAuthenticated;

  // Check for online status
  useEffect(() => {
    const handleOnlineStatus = () => setIsOffline(!navigator.onLine);
    
    // Initial check
    handleOnlineStatus();
    
    // Event listeners
    window.addEventListener('online', handleOnlineStatus);
    window.addEventListener('offline', handleOnlineStatus);
    
    return () => {
      window.removeEventListener('online', handleOnlineStatus);
      window.removeEventListener('offline', handleOnlineStatus);
    };
  }, []);

  // Fetch events data
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        
        const apiUrl = new URL(`${import.meta.env.VITE_API_URL}/api/events/`);
        
        // Add query parameter to filter by user if authenticated
        if (isAuthenticated && user) {
          apiUrl.searchParams.append('owner', user.id.toString());
        }
        
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
        };
        
        if (token) {
          headers['Authorization'] = `Token ${token}`;
        }
        
        const response = await fetch(apiUrl.toString(), { headers });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch events: ${response.status}`);
        }
        
        const data = await response.json();
        setEvents(data);
        setError(null);
      } catch (err) {
        console.error("Error fetching events:", err);
        // We don't show the error message anymore, but still track it in state
        setError('Failed to load events');
        setEvents([]); // Set empty events on error
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
  }, [isAuthenticated, token, user]);

  // Feature component
  const Feature = ({ icon, title, description }: FeatureProps) => (
    <div className="flex flex-col items-center text-center p-6 bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="text-blue-600 mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-semibold mb-2 text-gray-800">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );

  // Event card component
  const EventCard = ({ event }: { event: Event }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow duration-200">
      <div className="p-6">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-xl font-semibold text-gray-800 line-clamp-1">{event.name}</h3>
          {event.is_full && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
              Full
            </span>
          )}
        </div>
        
        <p className="text-gray-600 line-clamp-2 mb-4 text-sm">{event.description || "No description available"}</p>
        
        <div className="text-sm text-gray-500 space-y-1 mb-4">
          <div className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span>{event.date} • {event.time}</span>
          </div>
          
          <div className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="truncate">{event.location}</span>
          </div>
          
          <div className="flex items-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <span>
              {event.attendee_count} / {event.max_attendees ? event.max_attendees : '∞'} attendees
            </span>
          </div>
        </div>
        
        <div className="flex justify-between mt-4">
          <Link 
            to={`/events/${event.id}`}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            View Details
          </Link>
          {isAuthenticated && (
            <Link 
              to={`/events/${event.id}/check-in`}
              className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors"
            >
              Check-in
            </Link>
          )}
        </div>
      </div>
    </div>
  );

  // Skeleton loading card component
  const SkeletonCard = ({ key }: { key: number }) => (
    <div className="bg-white rounded border border-gray-200 p-2 animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
      <div className="h-2 bg-gray-200 rounded w-full mb-1"></div>
      <div className="space-y-1 mb-2">
        <div className="h-2 bg-gray-200 rounded w-2/3"></div>
        <div className="h-2 bg-gray-200 rounded w-1/2"></div>
      </div>
      <div className="flex justify-between">
        <div className="h-3 bg-gray-200 rounded w-16"></div>
        <div className="h-4 bg-gray-200 rounded w-12"></div>
      </div>
    </div>
  );

  // Testimonial component
  const Testimonial = ({ quote, author, role }: { quote: string, author: string, role: string }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
      <div className="flex mb-4 text-yellow-400">
        {[...Array(5)].map((_, i) => (
          <svg key={i} xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
      <p className="text-gray-600 italic mb-4">"{quote}"</p>
      <div>
        <p className="font-semibold text-gray-800">{author}</p>
        <p className="text-gray-500 text-sm">{role}</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section - Only for non-authenticated users */}
      {showMarketingContent && (
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
          <div className="max-w-6xl mx-auto px-4 py-16 sm:py-24">
            <div className="flex flex-col md:flex-row items-center">
              <div className="md:w-1/2 text-center md:text-left mb-10 md:mb-0">
                <h1 className="text-4xl sm:text-5xl font-bold mb-6">Streamline Your Event Check-ins</h1>
                <p className="text-xl opacity-90 max-w-2xl mb-8">
                  Ditch paper lists and manual tracking. Our QR Check-in System helps event organizers manage attendees efficiently with digital check-ins, real-time analytics, and seamless registration.
                </p>
                
                <div className="flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
                  <>
                    <Link 
                      to="/login" 
                      className="flex items-center justify-center gap-2 bg-white text-blue-700 px-6 py-3 rounded-lg shadow-sm hover:bg-gray-100 transition-colors font-medium"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                      </svg>
                      <span>Get Started</span>
                    </Link>
                    <Link 
                      to="/register" 
                      className="flex items-center justify-center gap-2 bg-transparent text-white border border-white px-6 py-3 rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
                      </svg>
                      <span>Create Account</span>
                    </Link>
                  </>
                </div>
                
                {isOffline && (
                  <div className="mt-6 inline-block py-2 px-4 bg-yellow-500 bg-opacity-20 text-yellow-100 rounded-lg border border-yellow-400 border-opacity-40">
                    <div className="flex items-center space-x-2">
                      <div className="h-2.5 w-2.5 rounded-full bg-yellow-300 animate-pulse"></div>
                      <span>You are currently offline. Limited functionality available.</span>
                    </div>
                  </div>
                )}
              </div>
              <div className="md:w-1/2">
                <div className="bg-white bg-opacity-10 p-6 rounded-xl border border-white border-opacity-20 shadow-lg">
                  <div className="relative">
                    <div className="aspect-w-16 aspect-h-9 rounded-lg overflow-hidden bg-black bg-opacity-50 flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 text-white opacity-70" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="rounded-full h-16 w-16 bg-blue-600 flex items-center justify-center shadow-lg cursor-pointer hover:bg-blue-700 transition-colors">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                          </svg>
                        </div>
                      </div>
                    </div>
                    <div className="absolute -bottom-4 -right-4 bg-yellow-400 text-blue-900 font-bold py-1 px-3 rounded-full text-sm">
                      See it in action
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Marketing sections - only for non-authenticated users */}
      {showMarketingContent && (
        <>
          {/* How It Works Section */}
          <div className="py-16 bg-white">
            <div className="max-w-6xl mx-auto px-4">
              <div className="text-center mb-12">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">How It Works</h2>
                <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                  Our platform simplifies event management from registration to analysis
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold mb-2">1. Create Event</h3>
                  <p className="text-gray-600">Set up your event with details, date, location, and attendee capacity in minutes.</p>
                </div>
                
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold mb-2">2. Register Attendees</h3>
                  <p className="text-gray-600">Collect registrations through your website or import your existing attendee list.</p>
                </div>
                
                <div className="flex flex-col items-center text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 mb-4">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold mb-2">3. Check-in Attendees</h3>
                  <p className="text-gray-600">Quickly scan QR codes or search by name for fast, secure check-ins at your event.</p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Features Section */}
          <div className="py-16 bg-gray-50">
            <div className="max-w-6xl mx-auto px-4">
              <div className="text-center mb-12">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Key Features</h2>
                <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                  Everything you need to run successful events
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                <Feature 
                  icon={
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                    </svg>
                  }
                  title="QR Code Check-ins"
                  description="Eliminate lines and manual tracking with our lightning-fast QR code scanning system for attendee check-ins."
                />
                
                <Feature 
                  icon={
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  }
                  title="Real-time Analytics"
                  description="Monitor attendance rates, check-in times, and attendee demographics in real-time during your event."
                />
                
                <Feature 
                  icon={
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                    </svg>
                  }
                  title="Attendee Communication"
                  description="Send automated confirmations, reminders, and post-event follow-ups to keep attendees informed."
                />
                
                <Feature 
                  icon={
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  }
                  title="Secure Access Control"
                  description="Prevent unauthorized entry with secure verification and optional identity checks at entry points."
                />
                
                <Feature 
                  icon={
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                    </svg>
                  }
                  title="Event Management"
                  description="Organize multiple events, manage staff permissions, and handle capacity limits all in one place."
                />
                
                <Feature 
                  icon={
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
                    </svg>
                  }
                  title="Integration Ready"
                  description="Connect with your existing tools like Mailchimp, Salesforce, or Google Sheets for a seamless workflow."
                />
              </div>
            </div>
          </div>
          
          {/* Testimonials */}
          <div className="py-16 bg-white">
            <div className="max-w-6xl mx-auto px-4">
              <div className="text-center mb-12">
                <h2 className="text-3xl font-bold text-gray-900 mb-4">What Our Users Say</h2>
                <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                  Event organizers love our simple but powerful check-in solution
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <Testimonial 
                  quote="We cut our check-in time by 70% and eliminated lines at our annual conference. This system paid for itself on day one."
                  author="Sarah Johnson"
                  role="Conference Director"
                />
                
                <Testimonial 
                  quote="The analytics alone make this worth it. We finally understand our attendance patterns and can plan better events as a result."
                  author="Michael Chen"
                  role="Event Coordinator"
                />
                
                <Testimonial 
                  quote="Easy to set up, even easier to use. Our staff picked it up in minutes and our attendees love the professional experience."
                  author="Jessica Williams"
                  role="Corporate Events Manager"
                />
              </div>
            </div>
          </div>

          {/* CTA Section */}
          <div className="py-16 bg-blue-700 text-white">
            <div className="max-w-4xl mx-auto px-4 text-center">
              <h2 className="text-3xl font-bold mb-6">Ready to transform your event check-ins?</h2>
              <p className="text-xl opacity-90 mb-8">
                Join thousands of event organizers who have simplified their check-in process
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <>
                  <Link 
                    to="/register" 
                    className="flex items-center justify-center gap-2 bg-white text-blue-700 px-6 py-3 rounded-lg shadow-sm hover:bg-gray-100 transition-colors font-medium"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
                    </svg>
                    <span>Sign Up Free</span>
                  </Link>
                  <Link 
                    to="/login" 
                    className="flex items-center justify-center gap-2 bg-transparent text-white border border-white px-6 py-3 rounded-lg hover:bg-white hover:bg-opacity-10 transition-colors"
                  >
                    <span>Learn More</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </Link>
                </>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Your Events Section */}
      <div className="py-16 bg-gray-50">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col sm:flex-row justify-between items-center mb-8 gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-800">
                {isAuthenticated ? 'Your Events' : 'Example Events'}
              </h2>
              {isAuthenticated ? (
                <p className="text-sm text-gray-600 mt-1">
                  Events you've created and manage
                </p>
              ) : (
                <p className="text-sm text-gray-600 mt-1">
                  Sign up to create and manage your own events
                </p>
              )}
            </div>
            
            {isAuthenticated ? (
              <Link 
                to="/events/new" 
                className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
                <span>Create Event</span>
              </Link>
            ) : (
              <Link 
                to="/login" 
                className="flex items-center gap-2 bg-blue-600 text-white px-5 py-2.5 rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                <span>Login to Create Events</span>
              </Link>
            )}
          </div>

          {/* Content Area with Conditional Rendering */}
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {[1, 2, 3, 4].map((index) => (
                <div key={index} className="bg-white rounded border border-gray-200 p-2 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-1"></div>
                  <div className="h-2 bg-gray-200 rounded w-full mb-1"></div>
                  <div className="space-y-1 mb-2">
                    <div className="h-2 bg-gray-200 rounded w-2/3"></div>
                    <div className="h-2 bg-gray-200 rounded w-1/2"></div>
                  </div>
                  <div className="flex justify-between">
                    <div className="h-3 bg-gray-200 rounded w-16"></div>
                    <div className="h-4 bg-gray-200 rounded w-12"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : events.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {events.map(event => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto mb-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 className="text-2xl font-semibold mb-2">Welcome to QR Check-in System</h3>
              <p className="text-gray-500 mb-6">
                {isAuthenticated 
                  ? "You're logged in. Start by creating your first event!"
                  : "Sign in to create and manage your own events."
                }
              </p>
              {isAuthenticated ? (
                <Link 
                  to="/events/new" 
                  className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                  </svg>
                  <span>Create your first event</span>
                </Link>
              ) : (
                <Link 
                  to="/login" 
                  className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 011 1v12a1 1 0 11-2 0V4a1 1 0 011-1zm7.707 3.293a1 1 0 010 1.414L9.414 9H17a1 1 0 110 2H9.414l1.293 1.293a1 1 0 01-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span>Sign in to create events</span>
                </Link>
              )}
            </div>
          )}
        </div>
      </div>

      {/* FAQ Section - only for non-authenticated users */}
      {showMarketingContent && (
        <div className="py-16 bg-white">
          <div className="max-w-4xl mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">Frequently Asked Questions</h2>
              <p className="text-xl text-gray-600">
                Common questions about our event check-in system
              </p>
            </div>
            
            <div className="space-y-6">
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-2">How does the QR code check-in work?</h3>
                <p className="text-gray-600">
                  When attendees register, our system generates a unique QR code for each person. At your event, simply scan their code with our mobile app to instantly check them in and update your attendance records.
                </p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-2">Can I use this for both free and paid events?</h3>
                <p className="text-gray-600">
                  Absolutely! Our system works for any type of event, whether free or paid. For paid events, you can integrate with popular payment processors to handle transactions seamlessly.
                </p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-2">What if attendees don't have smartphones?</h3>
                <p className="text-gray-600">
                  No problem! You can always search for attendees by name, email, or ticket ID in the system. We also provide options for printing attendee lists with QR codes for your check-in staff.
                </p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-2">Does it work without internet connection?</h3>
                <p className="text-gray-600">
                  Yes, our mobile app includes an offline mode that allows you to continue checking in attendees even without internet access. The data will sync automatically once you're back online.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer CTA - only for non-authenticated users */}
      {showMarketingContent && (
        <div className="bg-blue-600 py-12">
          <div className="max-w-6xl mx-auto px-4 text-center">
            <h2 className="text-2xl font-bold text-white mb-6">Get Started with QR Check-in Today</h2>
            <p className="text-white text-lg opacity-90 mb-8 max-w-2xl mx-auto">
              Join thousands of event organizers who are saving time and improving their events with our powerful check-in system.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <>
                <Link 
                  to="/register" 
                  className="bg-white text-blue-600 px-8 py-3 rounded-lg font-medium hover:bg-gray-100 transition-colors shadow-md"
                >
                  Sign Up Free
                </Link>
                <Link 
                  to="/contact" 
                  className="bg-transparent text-white border border-white px-8 py-3 rounded-lg font-medium hover:bg-white hover:bg-opacity-10 transition-colors"
                >
                  Contact Sales
                </Link>
              </>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}