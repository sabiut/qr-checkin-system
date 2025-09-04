import { useState, useEffect, useContext } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import QrCodeScanner from '../components/QrCodeScanner';
import { AuthContext } from '../context/AuthContext';
import { 
  Calendar, 
  Clock, 
  MapPin, 
  WifiOff, 
  Check, 
  AlertCircle, 
  UserCheck, 
  ChevronLeft, 
  RefreshCw, 
  QrCode, 
  Loader2,
  Info
} from 'lucide-react';

interface Event {
  id: number;
  name: string;
  date: string;
  time?: string;
  location: string;
}

interface Guest {
  id: string;
  guest_name: string;
  guest_email: string;
  guest_phone?: string;
  event_id: number;
}

export default function CheckIn() {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const { token, isAuthenticated } = useContext(AuthContext);
  
  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [checkInStatus, setCheckInStatus] = useState<'success' | 'error' | null>(null);
  const [guest, setGuest] = useState<Guest | null>(null);
  const [isOffline, setIsOffline] = useState(typeof navigator !== 'undefined' ? !navigator.onLine : false);
  const [offlineCheckIns, setOfflineCheckIns] = useState<string[]>([]);
  const [isSyncing, setIsSyncing] = useState(false);
  
  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Format date for display
  const formattedDate = event?.date 
    ? new Date(event.date).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    : '';

  // Check online status
  useEffect(() => {
    const handleOnline = () => {
      setIsOffline(false);
      // Don't auto-sync to avoid unexpected API calls
    };
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Load stored offline check-ins
    if (typeof window !== 'undefined' && window.localStorage) {
      const storedCheckIns = localStorage.getItem('offline_checkins');
      if (storedCheckIns) {
        setOfflineCheckIns(JSON.parse(storedCheckIns));
      }
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Load event data
  useEffect(() => {
    const fetchEvent = async () => {
      if (!eventId) return;
      
      try {
        setLoading(true);
        
        // Try to get from local storage first (for offline mode)
        let cachedEvents = null;
        if (typeof window !== 'undefined' && window.localStorage) {
          cachedEvents = localStorage.getItem('events');
          
          if (cachedEvents) {
            const parsedEvents = JSON.parse(cachedEvents);
            const foundEvent = parsedEvents.find((e: Event) => e.id.toString() === eventId);
            
            if (foundEvent) {
              setEvent(foundEvent);
              setLoading(false);
              return;
            }
          }
        }
        
        // Otherwise fetch from API
        if (!isOffline) {
          // Prepare headers with authentication token
          const headers: HeadersInit = {
            'Content-Type': 'application/json',
          };
          
          // Add authentication token if available
          if (token) {
            headers['Authorization'] = `Token ${token}`;
          }
          
          const response = await fetch(`${import.meta.env.VITE_API_URL}/api/events/${eventId}/`, {
            headers
          });
          
          // Check if response is HTML instead of JSON
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('text/html')) {
            throw new Error('Server returned HTML instead of JSON. Check API connection.');
          }
          
          if (!response.ok) {
            throw new Error(`Failed to fetch event: ${response.status} ${response.statusText}`);
          }
          
          const data = await response.json();
          setEvent(data);
          
          // Update the cached events if browser environment
          if (typeof window !== 'undefined' && window.localStorage) {
            if (cachedEvents) {
              const parsedEvents = JSON.parse(cachedEvents);
              const updatedEvents = parsedEvents.map((e: Event) => 
                e.id.toString() === eventId ? data : e
              );
              localStorage.setItem('events', JSON.stringify(updatedEvents));
            } else {
              // Create new cache if none exists
              localStorage.setItem('events', JSON.stringify([data]));
            }
          }
        } else if (!cachedEvents) {
          // No cached data and offline
          setError('No event data available offline. Connect to the internet to load event details.');
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Could not load event information';
        setError(errorMessage);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchEvent();
  }, [eventId, isOffline]);

  const handleScanSuccess = async (decodedText: string) => {
    setScanResult(decodedText);
    console.log("QR Code scanned:", decodedText);
    
    try {
      setIsSubmitting(true);
      
      // Clean up the decoded text - remove any quotes or whitespace
      let cleanedText = decodedText.trim();
      if (cleanedText.startsWith('"') && cleanedText.endsWith('"')) {
        cleanedText = cleanedText.slice(1, -1);
      }
      
      console.log("Cleaned QR code data:", cleanedText);
      
      // If offline, store the check-in locally
      if (isOffline) {
        handleOfflineCheckIn(cleanedText);
        return;
      }
      
      // Otherwise process online
      await processCheckIn(cleanedText);
    } catch (err) {
      setCheckInStatus('error');
      const errorMessage = err instanceof Error ? err.message : 'Failed to process check-in';
      setError(errorMessage);
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOfflineCheckIn = (invitationId: string) => {
    // Check if this ID has already been checked in offline
    if (offlineCheckIns.includes(invitationId)) {
      setCheckInStatus('error');
      setError('This guest has already been checked in (offline mode)');
      return;
    }
    
    // Store in local array
    const updatedCheckIns = [...offlineCheckIns, invitationId];
    setOfflineCheckIns(updatedCheckIns);
    
    // Save to localStorage if available
    if (typeof window !== 'undefined' && window.localStorage) {
      localStorage.setItem('offline_checkins', JSON.stringify(updatedCheckIns));
    }
    
    // Show success message
    setCheckInStatus('success');
    setGuest({
      id: invitationId,
      guest_name: 'Guest (Offline Mode)',
      guest_email: '',
      event_id: Number(eventId)
    });
  };

  const processCheckIn = async (invitationId: string) => {
    // Log the check-in attempt
    console.log(`Attempting to check in invitation ID: ${invitationId}`);
    
    try {
      const apiUrl = `${import.meta.env.VITE_API_URL}/api/attendance/check_in/`;
      console.log(`Sending check-in request to: ${apiUrl}`);
      
      const requestData = { invitation_id: invitationId };
      console.log('Request payload:', requestData);
      
      // Prepare headers with authentication token
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
      
      // Add authentication token if available
      if (token) {
        headers['Authorization'] = `Token ${token}`;
      }
      
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers,
        body: JSON.stringify(requestData),
      });
      
      console.log('Response status:', response.status, response.statusText);
      
      // Check if response is HTML instead of JSON
      const contentType = response.headers.get('content-type');
      console.log('Response content-type:', contentType);
      
      if (contentType && contentType.includes('text/html')) {
        console.error('Server returned HTML instead of JSON');
        throw new Error('Server returned HTML instead of JSON. Check API connection.');
      }
      
      // Safely parse the response
      let data;
      try {
        const text = await response.text();
        console.log('Response text:', text.substring(0, 200)); // Log first 200 chars
        data = JSON.parse(text);
      } catch (parseError) {
        console.error('Error parsing response:', parseError);
        throw new Error('Could not parse server response');
      }
      
      if (!response.ok) {
        console.error('Error response from server:', data);
        throw new Error(data.error || `Check-in failed with status ${response.status}`);
      }
      
      console.log('Check-in successful:', data);
      setCheckInStatus('success');
      
      // Set guest info from the response
      if (data.attendance?.invitation_details) {
        setGuest({
          id: invitationId,
          guest_name: data.attendance.invitation_details.guest_name,
          guest_email: data.attendance.invitation_details.guest_email || '',
          guest_phone: data.attendance.invitation_details.guest_phone || '',
          event_id: data.attendance.invitation_details.event
        });
      } else {
        console.warn('Response missing expected invitation details:', data);
        // Provide a fallback guest information
        setGuest({
          id: invitationId,
          guest_name: 'Guest',
          guest_email: '',
          event_id: Number(eventId)
        });
      }
    } catch (error) {
      console.error('Error during check-in processing:', error);
      throw error;
    }
  };

  const syncOfflineCheckIns = async () => {
    if (offlineCheckIns.length === 0 || isOffline) return;
    
    setIsSyncing(true);
    
    try {
      let successCount = 0;
      let failCount = 0;
      
      // Process all stored offline check-ins
      for (const invitationId of offlineCheckIns) {
        try {
          // Prepare headers with authentication token
          const headers: HeadersInit = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          };
          
          // Add authentication token if available
          if (token) {
            headers['Authorization'] = `Token ${token}`;
          }
          
          await fetch(`${import.meta.env.VITE_API_URL}/api/attendance/check_in/`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ invitation_id: invitationId }),
          });
          successCount++;
        } catch (err) {
          console.error(`Failed to sync check-in ${invitationId}:`, err);
          failCount++;
        }
      }
      
      // Clear offline storage after sync
      setOfflineCheckIns([]);
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.removeItem('offline_checkins');
      }
      
      // Show notification (this could be enhanced with a toast notification)
      alert(`Synced ${successCount} check-ins successfully. ${failCount > 0 ? `${failCount} failed.` : ''}`);
    } catch (err) {
      console.error('Error during sync:', err);
      alert('Error during sync. Some check-ins may not have been processed.');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleReset = () => {
    setScanResult(null);
    setCheckInStatus(null);
    setGuest(null);
    setError(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 size={40} className="animate-spin mx-auto text-blue-600 mb-4" />
          <p className="text-gray-600">Loading event information...</p>
        </div>
      </div>
    );
  }

  if (error && !checkInStatus) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with navigation */}
      <header className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <button 
                onClick={() => navigate(-1)}
                className="text-gray-600 hover:text-gray-900 p-2 rounded-full hover:bg-gray-100 mr-2"
              >
                <ChevronLeft size={20} />
              </button>
              <h1 className="text-xl font-bold text-gray-900">Event Check-in</h1>
            </div>
            {isOffline && (
              <div className="flex items-center gap-1.5 px-3 py-1 bg-yellow-50 text-yellow-800 rounded-full text-sm">
                <WifiOff size={16} />
                <span>Offline Mode</span>
              </div>
            )}
          </div>
        </div>
      </header>
      
      <div className="max-w-2xl mx-auto p-4 pt-6">
        {/* Event details card */}
        {event && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-3">{event.name}</h2>
            <div className="space-y-3">
              <div className="flex items-center text-gray-600">
                <Calendar size={18} className="mr-2 text-blue-600" />
                <span>{formattedDate}</span>
              </div>
              {event.time && (
                <div className="flex items-center text-gray-600">
                  <Clock size={18} className="mr-2 text-blue-600" />
                  <span>{event.time}</span>
                </div>
              )}
              <div className="flex items-center text-gray-600">
                <MapPin size={18} className="mr-2 text-blue-600" />
                <span>{event.location}</span>
              </div>
            </div>
          </div>
        )}
        
        {/* Offline check-ins notification */}
        {offlineCheckIns.length > 0 && !isOffline && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="text-blue-500 mt-0.5">
                <Info size={20} />
              </div>
              <div>
                <h3 className="font-medium text-blue-800">Pending offline check-ins</h3>
                <p className="text-blue-700 text-sm">
                  You have {offlineCheckIns.length} {offlineCheckIns.length === 1 ? 'check-in' : 'check-ins'} ready to be synchronized.
                </p>
              </div>
            </div>
            <button 
              onClick={syncOfflineCheckIns}
              disabled={isSyncing}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 min-w-32"
            >
              {isSyncing ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>Syncing...</span>
                </>
              ) : (
                <>
                  <RefreshCw size={16} />
                  <span>Sync Now</span>
                </>
              )}
            </button>
          </div>
        )}
        
        {/* Check-in result card */}
        {checkInStatus && (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden mb-6">
            <div className={`p-5 ${
              checkInStatus === 'success' 
                ? 'bg-green-50 border-b border-green-100' 
                : 'bg-red-50 border-b border-red-100'
            }`}>
              <div className="flex items-start">
                <div className={`flex-shrink-0 rounded-full p-2 ${
                  checkInStatus === 'success' ? 'bg-green-100' : 'bg-red-100'
                }`}>
                  {checkInStatus === 'success' ? (
                    <Check size={20} className="text-green-600" />
                  ) : (
                    <AlertCircle size={20} className="text-red-600" />
                  )}
                </div>
                <div className="ml-3">
                  <h3 className={`text-lg font-semibold ${
                    checkInStatus === 'success' ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {checkInStatus === 'success' ? 'Check-in Successful!' : 'Check-in Failed'}
                  </h3>
                  <p className={checkInStatus === 'success' ? 'text-green-700' : 'text-red-700'}>
                    {checkInStatus === 'success' 
                      ? 'The guest has been checked in successfully.' 
                      : (error || 'There was a problem with this check-in.')}
                  </p>
                </div>
              </div>
            </div>
            
            {guest && checkInStatus === 'success' && (
              <div className="p-5">
                <h4 className="font-medium text-gray-700 mb-3">Guest Information</h4>
                <div className="space-y-2">
                  <div className="flex">
                    <span className="font-medium text-gray-500 w-24">Name:</span>
                    <span className="text-gray-900">{guest.guest_name}</span>
                  </div>
                  {guest.guest_email && (
                    <div className="flex">
                      <span className="font-medium text-gray-500 w-24">Email:</span>
                      <span className="text-gray-900">{guest.guest_email}</span>
                    </div>
                  )}
                  {guest.guest_phone && (
                    <div className="flex">
                      <span className="font-medium text-gray-500 w-24">Phone:</span>
                      <span className="text-gray-900">{guest.guest_phone}</span>
                    </div>
                  )}
                  {isOffline && (
                    <div className="mt-4 text-sm text-yellow-700 bg-yellow-50 p-2 rounded border border-yellow-200 flex items-center">
                      <WifiOff size={16} className="mr-2" />
                      This check-in will be synchronized when you're back online.
                    </div>
                  )}
                </div>
              </div>
            )}
            
            <div className="p-5 bg-gray-50 flex justify-center">
              <button
                onClick={handleReset}
                className="flex items-center justify-center gap-2 px-5 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                <QrCode size={18} />
                <span>Scan Another Code</span>
              </button>
            </div>
          </div>
        )}
        
        {/* QR Scanner */}
        {!checkInStatus && (
          <div className="bg-white rounded-xl shadow-sm overflow-hidden mb-6">
            <div className="p-5 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Scan QR Code</h2>
              <p className="text-gray-600 mt-1">
                Position the invitation QR code within the frame to check in a guest.
              </p>
            </div>
            
            <div className="p-4 flex justify-center bg-gray-50">
              <div className="max-w-md w-full overflow-hidden rounded-lg">
                <div className={`relative ${isSubmitting ? 'opacity-60' : ''}`}>
                  <QrCodeScanner onScanSuccess={handleScanSuccess} />
                  
                  {isSubmitting && (
                    <div className="absolute inset-0 flex items-center justify-center bg-black/30 rounded">
                      <div className="bg-white p-3 rounded-lg flex items-center gap-3">
                        <Loader2 size={24} className="animate-spin text-blue-600" />
                        <span className="font-medium">Processing...</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="p-4 border-t">
              <p className="text-sm text-gray-500 text-center">
                When scanned successfully, the guest will be checked in automatically.
              </p>
            </div>
          </div>
        )}
        
        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-between">
          <Link
            to={`/events/${eventId}`}
            className="flex items-center justify-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <ChevronLeft size={18} />
            <span>Back to Event</span>
          </Link>
          
          <button
            onClick={() => window.location.reload()}
            className="flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-800 text-white rounded-lg hover:bg-gray-900 transition-colors"
          >
            <RefreshCw size={18} />
            <span>Reset Scanner</span>
          </button>
        </div>
      </div>
    </div>
  );
}