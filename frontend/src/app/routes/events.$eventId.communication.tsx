import React from 'react';
import { useParams } from 'react-router';
import { CommunicationHub } from '../components/CommunicationHub';
import ProtectedRoute from '../components/ProtectedRoute';

export default function EventCommunication() {
  const { eventId } = useParams();

  console.log('EventCommunication component loaded, eventId:', eventId);

  if (!eventId) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-600 text-xl">Event ID not found</div>
      </div>
    );
  }

  try {
    return (
      <ProtectedRoute>
        <CommunicationHub eventId={eventId} />
      </ProtectedRoute>
    );
  } catch (error) {
    console.error('Error rendering EventCommunication:', error);
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-600 text-xl">
          Error loading communication hub: {error?.toString()}
        </div>
      </div>
    );
  }
}