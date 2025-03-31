import { useState, useEffect } from 'react';
import { SyncService } from '../services/SyncService';

const SyncStatus = () => {
  const [isOffline, setIsOffline] = useState(false);
  const [pendingEvents, setPendingEvents] = useState(0);
  const [pendingInvitations, setPendingInvitations] = useState(0);
  const [pendingCheckIns, setPendingCheckIns] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null);
  const [isBrowser, setIsBrowser] = useState(false);
  
  // Check if we're in the browser
  useEffect(() => {
    setIsBrowser(true);
    if (typeof navigator !== 'undefined') {
      setIsOffline(!navigator.onLine);
    }
  }, []);
  
  // Check online status and count pending items
  useEffect(() => {
    if (!isBrowser) return;
    
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    const countPendingItems = () => {
      try {
        if (typeof window === 'undefined' || !window.localStorage) return;
        
        // Count pending events
        const events = JSON.parse(localStorage.getItem('pending_events') || '[]');
        setPendingEvents(events.length);
        
        // Count pending invitations
        const invitations = JSON.parse(localStorage.getItem('pending_invitations') || '[]');
        setPendingInvitations(invitations.length);
        
        // Count pending check-ins
        const checkIns = JSON.parse(localStorage.getItem('offline_checkins') || '[]');
        setPendingCheckIns(checkIns.length);
      } catch (error) {
        console.error('Error counting pending items:', error);
      }
    };
    
    countPendingItems();
    
    // Set up interval to periodically count pending items
    const interval = setInterval(countPendingItems, 5000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, [isBrowser]);
  
  const handleSync = async () => {
    if (!isBrowser || isOffline) {
      setSyncMessage({ 
        text: "Cannot sync while offline. Please try again when you're connected to the internet.", 
        type: 'error' 
      });
      return;
    }
    
    setIsSyncing(true);
    setSyncMessage(null);
    
    try {
      const result = await SyncService.syncAll();
      setSyncMessage({ 
        text: result.message, 
        type: result.success ? 'success' : 'error' 
      });
      
      // Recount after sync
      setPendingEvents(0);
      setPendingInvitations(0);
      setPendingCheckIns(0);
    } catch (error) {
      setSyncMessage({ 
        text: `Sync failed: ${error instanceof Error ? error.message : String(error)}`, 
        type: 'error' 
      });
    } finally {
      setIsSyncing(false);
    }
  };
  
  const totalPending = pendingEvents + pendingInvitations + pendingCheckIns;
  
  // Don't render anything during SSR
  if (!isBrowser) {
    return null;
  }
  
  // Don't show anything if there's nothing to sync and we're online
  if (totalPending === 0 && !isOffline) {
    return null;
  }
  
  return (
    <div className="fixed bottom-4 right-4 z-50">
      <div className="bg-white rounded-lg shadow-lg p-4 max-w-xs w-full">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-medium text-gray-800">
            {isOffline ? 'Offline Mode' : 'Sync Status'}
          </h3>
          <div className={`w-3 h-3 rounded-full ${isOffline ? 'bg-red-500' : 'bg-green-500'}`}></div>
        </div>
        
        {totalPending > 0 && (
          <div className="mb-3 text-sm text-gray-600">
            <p>Pending changes to sync:</p>
            <ul className="ml-4 mt-1 list-disc">
              {pendingEvents > 0 && (
                <li>{pendingEvents} event{pendingEvents !== 1 ? 's' : ''}</li>
              )}
              {pendingInvitations > 0 && (
                <li>{pendingInvitations} invitation{pendingInvitations !== 1 ? 's' : ''}</li>
              )}
              {pendingCheckIns > 0 && (
                <li>{pendingCheckIns} check-in{pendingCheckIns !== 1 ? 's' : ''}</li>
              )}
            </ul>
          </div>
        )}
        
        {syncMessage && (
          <div className={`text-sm p-2 mb-3 rounded ${
            syncMessage.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {syncMessage.text}
          </div>
        )}
        
        <button
          onClick={handleSync}
          disabled={isOffline || isSyncing || totalPending === 0}
          className={`w-full py-2 px-4 rounded text-white text-sm ${
            isOffline || totalPending === 0 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isSyncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>
    </div>
  );
};

export default SyncStatus;