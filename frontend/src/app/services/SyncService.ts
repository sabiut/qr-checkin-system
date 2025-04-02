/**
 * Service to handle offline data synchronization with the backend
 */
export const SyncService = {
  /**
   * Get the authentication token from local storage
   */
  getAuthToken(): string | null {
    if (typeof window === 'undefined' || !window.localStorage) {
      return null;
    }
    return localStorage.getItem('auth_token');
  },
  /**
   * Synchronize all local offline data with the server
   */
  async syncAll(): Promise<{ success: boolean; message: string }> {
    try {
      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        return { 
          success: false, 
          message: "Cannot sync while offline. Please try again when you're connected to the internet."
        };
      }
      
      // Check if we're in a browser environment
      if (typeof window === 'undefined' || !window.localStorage) {
        return {
          success: false,
          message: "Synchronization is not available in this environment."
        };
      }
      
      // Sync in this order: events, invitations, check-ins
      await this.syncEvents();
      await this.syncInvitations();
      await this.syncCheckIns();
      
      return { success: true, message: "All data synchronized successfully!" };
    } catch (error) {
      console.error("Sync error:", error);
      return { 
        success: false, 
        message: `Synchronization failed: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  },
  
  /**
   * Synchronize offline events with the server
   */
  async syncEvents(): Promise<void> {
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    
    const pendingEvents = JSON.parse(localStorage.getItem('pending_events') || '[]');
    
    if (pendingEvents.length === 0) {
      return;
    }
    
    try {
      const authToken = this.getAuthToken();
      if (!authToken) {
        throw new Error('Authentication required to sync events');
      }
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/events/sync/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify(pendingEvents),
      });
      
      if (!response.ok) {
        throw new Error('Failed to sync events');
      }
      
      const data = await response.json();
      const idMapping = data.id_mapping || {};
      
      // Update stored events with real IDs
      const cachedEvents = JSON.parse(localStorage.getItem('events') || '[]');
      const updatedEvents = cachedEvents.map((event: any) => {
        if (idMapping[event.id]) {
          return { ...event, id: idMapping[event.id] };
        }
        return event;
      });
      
      localStorage.setItem('events', JSON.stringify(updatedEvents));
      localStorage.removeItem('pending_events');
    } catch (error) {
      console.error('Event sync error:', error);
      throw error;
    }
  },
  
  /**
   * Synchronize offline invitations with the server
   */
  async syncInvitations(): Promise<void> {
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    
    const pendingInvitations = JSON.parse(localStorage.getItem('pending_invitations') || '[]');
    
    if (pendingInvitations.length === 0) {
      return;
    }
    
    try {
      const authToken = this.getAuthToken();
      if (!authToken) {
        throw new Error('Authentication required to sync invitations');
      }
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/invitations/sync/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify(pendingInvitations),
      });
      
      if (!response.ok) {
        throw new Error('Failed to sync invitations');
      }
      
      const data = await response.json();
      const idMapping = data.id_mapping || {};
      
      // Update stored invitations with real IDs in each event's invitations cache
      const eventIds = [...new Set(pendingInvitations.map((inv: any) => inv.event_id))];
      
      for (const eventId of eventIds) {
        const key = `invitations_${eventId}`;
        const cachedInvitations = JSON.parse(localStorage.getItem(key) || '[]');
        
        const updatedInvitations = cachedInvitations.map((invitation: any) => {
          if (idMapping[invitation.id]) {
            return { ...invitation, id: idMapping[invitation.id] };
          }
          return invitation;
        });
        
        localStorage.setItem(key, JSON.stringify(updatedInvitations));
      }
      
      localStorage.removeItem('pending_invitations');
    } catch (error) {
      console.error('Invitation sync error:', error);
      throw error;
    }
  },
  
  /**
   * Synchronize offline check-ins with the server
   */
  async syncCheckIns(): Promise<void> {
    if (typeof window === 'undefined' || !window.localStorage) {
      return;
    }
    
    const offlineCheckIns = JSON.parse(localStorage.getItem('offline_checkins') || '[]');
    
    if (offlineCheckIns.length === 0) {
      return;
    }
    
    try {
      const authToken = this.getAuthToken();
      if (!authToken) {
        throw new Error('Authentication required to sync check-ins');
      }
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/attendance/sync-offline/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${authToken}`,
        },
        body: JSON.stringify({ invitation_ids: offlineCheckIns }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to sync check-ins');
      }
      
      localStorage.removeItem('offline_checkins');
    } catch (error) {
      console.error('Check-in sync error:', error);
      throw error;
    }
  }
};