import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import axios from "axios";

interface Invitation {
  id: string;
  guest_name: string;
  event_details: {
    name: string;
    date: string;
    time: string;
    location: string;
  };
  rsvp_status: string;
}

export default function RSVPPage() {
  const { invitationId } = useParams<{ invitationId: string }>();
  const [searchParams] = useSearchParams();
  const initialStatus = searchParams.get("status") || "PENDING";
  const navigate = useNavigate();
  
  const [invitation, setInvitation] = useState<Invitation | null>(null);
  const [status, setStatus] = useState(initialStatus);
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  
  useEffect(() => {
    // Get invitation details
    const fetchInvitation = async () => {
      try {
        const response = await axios.get(`/api/invitations/${invitationId}/`);
        setInvitation(response.data);
        setLoading(false);
      } catch (err) {
        setError("Could not find your invitation. It may have been removed or the link is invalid.");
        setLoading(false);
      }
    };
    
    fetchInvitation();
  }, [invitationId]);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      await axios.post(`/api/invitations/${invitationId}/rsvp_response/`, {
        status,
        notes
      });
      
      setSubmitted(true);
      setSubmitting(false);
    } catch (err) {
      setError("An error occurred while submitting your response. Please try again.");
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="p-6 max-w-sm w-full bg-white shadow-md rounded-lg">
          <div className="flex justify-center items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <span className="ml-2">Loading...</span>
          </div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="p-6 max-w-sm w-full bg-white shadow-md rounded-lg">
          <div className="text-red-500 text-center mb-4">{error}</div>
          <button 
            onClick={() => navigate("/")}
            className="w-full py-2 px-4 bg-indigo-600 text-white rounded hover:bg-indigo-700 focus:outline-none"
          >
            Return to Home
          </button>
        </div>
      </div>
    );
  }
  
  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="p-6 max-w-md w-full bg-white shadow-md rounded-lg">
          <h2 className="text-2xl font-bold text-center text-gray-800 mb-4">Thank You!</h2>
          <div className="text-center mb-4">
            <p className="text-green-600 font-semibold mb-2">Your RSVP has been recorded.</p>
            <p>We've noted your response for {invitation?.event_details.name}.</p>
            {status === "ATTENDING" && (
              <p className="mt-4">We look forward to seeing you there!</p>
            )}
            {status === "DECLINED" && (
              <p className="mt-4">We're sorry you can't make it, but thank you for letting us know.</p>
            )}
          </div>
          {status === "ATTENDING" && (
            <div className="bg-gray-50 p-4 rounded mb-4">
              <h3 className="font-semibold mb-2">Event Details:</h3>
              <p><span className="font-medium">Date:</span> {invitation?.event_details.date}</p>
              <p><span className="font-medium">Time:</span> {invitation?.event_details.time}</p>
              <p><span className="font-medium">Location:</span> {invitation?.event_details.location}</p>
            </div>
          )}
          <button 
            onClick={() => navigate("/")}
            className="w-full py-2 px-4 bg-indigo-600 text-white rounded hover:bg-indigo-700 focus:outline-none"
          >
            Return to Home
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full bg-white shadow-xl rounded-lg p-8">
        <div className="text-center mb-6">
          <h2 className="text-3xl font-bold text-gray-800">RSVP</h2>
          <p className="mt-2 text-gray-600">
            {invitation?.event_details.name}
          </p>
        </div>
        
        <div className="bg-gray-50 p-4 rounded mb-6">
          <h3 className="font-semibold mb-2">Event Details:</h3>
          <p><span className="font-medium">Date:</span> {invitation?.event_details.date}</p>
          <p><span className="font-medium">Time:</span> {invitation?.event_details.time}</p>
          <p><span className="font-medium">Location:</span> {invitation?.event_details.location}</p>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-gray-700 font-semibold mb-2">
              Will you attend?
            </label>
            <div className="flex flex-col gap-2">
              <div className={`p-3 border rounded cursor-pointer ${status === "ATTENDING" ? "border-green-500 bg-green-50" : "border-gray-300"}`}
                   onClick={() => setStatus("ATTENDING")}>
                <div className="flex items-center">
                  <div className={`w-4 h-4 rounded-full mr-2 ${status === "ATTENDING" ? "bg-green-500" : "border border-gray-400"}`}></div>
                  <span className="font-medium">Yes, I'll attend</span>
                </div>
              </div>
              <div className={`p-3 border rounded cursor-pointer ${status === "DECLINED" ? "border-red-500 bg-red-50" : "border-gray-300"}`}
                   onClick={() => setStatus("DECLINED")}>
                <div className="flex items-center">
                  <div className={`w-4 h-4 rounded-full mr-2 ${status === "DECLINED" ? "bg-red-500" : "border border-gray-400"}`}></div>
                  <span className="font-medium">No, I can't make it</span>
                </div>
              </div>
            </div>
          </div>
          
          <div className="mb-6">
            <label htmlFor="notes" className="block text-gray-700 font-semibold mb-2">
              Additional Notes (optional)
            </label>
            <textarea
              id="notes"
              placeholder="Any dietary requirements or other information?"
              className="w-full px-3 py-2 placeholder-gray-400 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            ></textarea>
          </div>
          
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3 px-4 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {submitting ? "Submitting..." : "Submit RSVP"}
          </button>
        </form>
      </div>
    </div>
  );
}