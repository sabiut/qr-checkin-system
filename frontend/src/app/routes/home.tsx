import { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

interface FeatureProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  stat?: string;
  bgColor?: string;
  iconColor?: string;
  borderColor?: string;
}

interface TestimonialProps {
  quote: string;
  author: string;
  role: string;
  company?: string;
  image?: string;
  logo?: string;
  metrics?: {
    attendees: string;
    timeSaved: string;
    satisfaction: string;
  };
}

export default function Home() {
  const [isOffline, setIsOffline] = useState(false);
  const [activeTestimonial, setActiveTestimonial] = useState(0);
  const [isHeroVisible, setIsHeroVisible] = useState(false);
  
  const { isAuthenticated, user } = useContext(AuthContext);
  
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

  // Animation effect for hero section
  useEffect(() => {
    setIsHeroVisible(true);
  }, []);

  // Auto-rotate testimonials
  useEffect(() => {
    if (showMarketingContent) {
      const interval = setInterval(() => {
        setActiveTestimonial((current) => (current + 1) % testimonials.length);
      }, 8000);
      
      return () => clearInterval(interval);
    }
  }, [showMarketingContent]);

  // Features data
  const features: FeatureProps[] = [
    {
      title: "QR Code Check-ins",
      description: "Eliminate lines with our lightning-fast QR scanning system that processes attendees in seconds.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
        </svg>
      ),
      stat: "70% faster check-ins",
      bgColor: "bg-blue-50",
      iconColor: "text-blue-600",
      borderColor: "border-blue-100"
    },
    {
      title: "Real-time Analytics",
      description: "Monitor attendance rates, check-in times, and attendee demographics as they happen during your event.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      stat: "Live insights",
      bgColor: "bg-indigo-50",
      iconColor: "text-indigo-600",
      borderColor: "border-indigo-100"
    },
    {
      title: "Attendee Communication",
      description: "Send automated confirmations, reminders, and post-event follow-ups with customizable templates.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
        </svg>
      ),
      stat: "99% open rate",
      bgColor: "bg-purple-50",
      iconColor: "text-purple-600",
      borderColor: "border-purple-100"
    },
    {
      title: "Secure Access Control",
      description: "Prevent unauthorized entry with verification and optional identity checks that update in real-time.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      ),
      stat: "Zero unauthorized entries",
      bgColor: "bg-green-50",
      iconColor: "text-green-600",
      borderColor: "border-green-100"
    },
    {
      title: "Multi-Event Management",
      description: "Organize multiple events, manage staff permissions, and handle capacity limits from one dashboard.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
        </svg>
      ),
      stat: "Unlimited events",
      bgColor: "bg-yellow-50",
      iconColor: "text-yellow-600",
      borderColor: "border-yellow-100"
    },
    {
      title: "Seamless Integrations",
      description: "Connect with your existing tools like Mailchimp, Google Sheets, or other platforms for workflow automation.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z" />
        </svg>
      ),
      stat: "20+ integrations",
      bgColor: "bg-red-50",
      iconColor: "text-red-600",
      borderColor: "border-red-100"
    }
  ];

  // Testimonials data
  const testimonials: TestimonialProps[] = [
    {
      quote: "We cut our check-in time by 70% and eliminated lines at our annual conference. The analytics dashboard gave us valuable insights we never had before.",
      author: "Sarah Johnson",
      role: "Conference Director",
      company: "TechSummit",
      image: "",
      logo: "",
      metrics: {
        attendees: "1,200+",
        timeSaved: "4.5 hours",
        satisfaction: "98%"
      }
    },
    {
      quote: "The QR code system was incredibly easy to set up. Our staff picked it up in minutes, and our attendees loved the professional experience.",
      author: "Michael Chen",
      role: "Event Coordinator",
      company: "Global Marketing Forum",
      image: "",
      logo: "",
      metrics: {
        attendees: "800+",
        timeSaved: "3 hours",
        satisfaction: "96%"
      }
    },
    {
      quote: "The analytics alone make this worth it. We now understand our attendance patterns and can plan better events based on real data.",
      author: "Jessica Williams",
      role: "Corporate Events Manager",
      company: "Enterprise Solutions Inc.",
      image: "",
      logo: "",
      metrics: {
        attendees: "500+",
        timeSaved: "2.5 hours",
        satisfaction: "99%"
      }
    }
  ];

  // How it works steps
  const howItWorksSteps = [
    {
      title: "Create Your Event",
      description: "Set up your event details, date, location, and capacity in minutes.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      ),
    },
    {
      title: "Register Attendees",
      description: "Collect registrations or import your existing attendee list.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
        </svg>
      ),
    },
    {
      title: "Generate QR Codes",
      description: "Each attendee receives a unique QR code for fast check-in.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
        </svg>
      ),
    },
    {
      title: "Check-in Attendees",
      description: "Quickly scan QR codes for fast, secure check-ins at your event.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
    },
    {
      title: "Monitor in Real-time",
      description: "Track attendance, manage capacity, and view real-time analytics.",
      icon: (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
  ];

  // FAQ data
  const faqItems = [
    {
      question: "How does the QR code check-in work?",
      answer: "When attendees register, our system generates a unique QR code for each person. At your event, simply scan their code with our mobile app to instantly check them in and update your attendance records. The entire process takes less than 2 seconds per attendee."
    },
    {
      question: "Can I use this for both free and paid events?",
      answer: "Absolutely! Our system works for any type of event, whether free or paid. For paid events, you can integrate with popular payment processors including Stripe, PayPal, and Square to handle transactions seamlessly."
    },
    {
      question: "What if attendees don't have smartphones?",
      answer: "No problem! You can always search for attendees by name, email, or ticket ID in the system. We also provide options for printing attendee lists with QR codes for your check-in staff to scan from printed tickets."
    },
    {
      question: "Does it work without internet connection?",
      answer: "Yes, our mobile app includes a robust offline mode that allows you to continue checking in attendees even without internet access. The data will sync automatically once you're back online, ensuring you never lose any check-in information."
    },
    {
      question: "How secure is the platform?",
      answer: "Security is our top priority. We use enterprise-grade encryption for all data, implement strict access controls, and are compliant with privacy regulations including GDPR. Your attendee data is always protected."
    }
  ];

  // Feature component
  const Feature = ({ icon, title, description, stat, bgColor = "bg-white", iconColor = "text-blue-600", borderColor = "border-gray-100" }: FeatureProps) => (
    <div className={`${bgColor} rounded-xl p-6 border ${borderColor} hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1`}>
      <div className={`${iconColor} mb-5`}>
        {icon}
      </div>
      
      <h3 className="text-xl font-bold mb-2 text-gray-800">{title}</h3>
      <p className="text-gray-700 mb-4">{description}</p>
      
      {stat && (
        <div className="bg-white bg-opacity-60 rounded-lg px-3 py-2 inline-block text-sm font-medium text-gray-800 shadow-sm">
          {stat}
        </div>
      )}
    </div>
  );

  // Testimonial component
  const Testimonial = ({ quote, author, role, company, logo, metrics }: TestimonialProps) => (
    <div className="bg-white rounded-xl p-6 shadow-md border border-gray-100 hover:shadow-lg transition-shadow">
      <div className="flex mb-4 text-yellow-400">
        {[...Array(5)].map((_, i) => (
          <svg key={i} xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
      
      <p className="text-gray-700 italic mb-4">"{quote}"</p>
      
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-3">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div>
            <p className="font-semibold text-gray-800">{author}</p>
            <p className="text-gray-500 text-sm">{role}</p>
          </div>
        </div>
        
        {logo && (
          <img 
            src={logo}
            alt={company || author}
            className="h-6"
          />
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Dashboard Section - Only for authenticated users */}
      {isAuthenticated && (
        <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-indigo-800 text-white shadow-xl">
          <div className="max-w-6xl mx-auto px-4 py-14 relative">
            {/* Abstract shapes for visual interest */}
            <div className="absolute inset-0 overflow-hidden opacity-10">
              <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-blue-400"></div>
              <div className="absolute top-40 -left-20 w-80 h-80 rounded-full bg-indigo-400"></div>
              <div className="absolute -bottom-40 right-40 w-96 h-96 rounded-full bg-purple-400"></div>
            </div>
            
            <div className="flex flex-col md:flex-row items-center justify-between relative z-10">
              <div>
                <h1 className="text-3xl md:text-4xl font-bold mb-3">Welcome, {user?.username || 'Event Organizer'}!</h1>
                <p className="text-blue-100 mb-8 text-lg">Manage your events and track attendees from your dashboard</p>
                
                <div className="flex flex-wrap gap-4">
                  <Link 
                    to="/events/new" 
                    className="flex items-center gap-2 bg-white text-blue-700 px-6 py-3 rounded-lg hover:bg-blue-50 transition-all duration-300 transform hover:-translate-y-1 shadow-lg font-medium"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                    </svg>
                    <span>Create New Event</span>
                  </Link>
                  
                  <Link 
                    to="/events" 
                    className="flex items-center gap-2 bg-blue-600 bg-opacity-30 text-white border border-blue-400 border-opacity-30 px-6 py-3 rounded-lg hover:bg-opacity-40 transition-all duration-300 transform hover:-translate-y-1 shadow-md backdrop-blur-sm"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                    <span>Manage Events</span>
                  </Link>
                  
                  <Link 
                    to="/dashboard" 
                    className="flex items-center gap-2 bg-blue-600 bg-opacity-30 text-white border border-blue-400 border-opacity-30 px-6 py-3 rounded-lg hover:bg-opacity-40 transition-all duration-300 transform hover:-translate-y-1 shadow-md backdrop-blur-sm"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                    <span>View Dashboard</span>
                  </Link>
                </div>
              </div>
              
              <div className="mt-16 md:mt-8 flex items-center p-6 bg-white bg-opacity-10 rounded-2xl border border-white border-opacity-20 shadow-xl backdrop-blur-sm hover:bg-opacity-15 transition-all duration-300 transform hover:-translate-y-1">
                <div className="mr-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-indigo-600 rounded-full flex items-center justify-center p-1 shadow-lg">
                    <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                      </svg>
                    </div>
                  </div>
                </div>
                <div>
                  <div className="font-semibold text-xl mb-2 text-white">Quick Tips</div>
                  <ul className="text-sm text-gray-800 space-y-2">
                    <li className="flex items-center">
                      <div className="w-5 h-5 rounded-full bg-gradient-to-r from-green-400 to-emerald-500 flex items-center justify-center mr-2 shadow-sm">
                        <svg className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <span>Create your first event</span>
                    </li>
                    <li className="flex items-center">
                      <div className="w-5 h-5 rounded-full bg-gradient-to-r from-green-400 to-emerald-500 flex items-center justify-center mr-2 shadow-sm">
                        <svg className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <span>Import your attendee list</span>
                    </li>
                    <li className="flex items-center">
                      <div className="w-5 h-5 rounded-full bg-gradient-to-r from-green-400 to-emerald-500 flex items-center justify-center mr-2 shadow-sm">
                        <svg className="h-3 w-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <span>Test the QR scanner</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
            
            {isOffline && (
              <div className="mt-8 inline-block py-3 px-5 bg-yellow-500 bg-opacity-20 text-yellow-100 rounded-lg border border-yellow-400 border-opacity-40 shadow-lg backdrop-blur-sm">
                <div className="flex items-center space-x-3">
                  <div className="h-3 w-3 rounded-full bg-yellow-300 animate-pulse"></div>
                  <span className="font-medium">You are currently offline. Limited functionality available.</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Hero Section - Only for non-authenticated users */}
      {showMarketingContent && (
        <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-indigo-800 text-white overflow-hidden">
          <div className="max-w-6xl mx-auto px-4 py-20 sm:py-28 relative">
            {/* Enhanced Background Elements */}
            <div className="absolute inset-0 overflow-hidden">
              <div className="absolute -top-40 right-0 w-96 h-96 rounded-full bg-blue-500 opacity-10 blur-3xl"></div>
              <div className="absolute bottom-0 -left-20 w-80 h-80 rounded-full bg-indigo-400 opacity-10 blur-3xl"></div>
              <div className="absolute top-60 right-20 w-40 h-40 rounded-full bg-purple-500 opacity-10 blur-2xl"></div>
              
              {/* Subtle grid pattern overlay */}
              <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black opacity-5"
                   style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 0h40v40H0V0zm20 20h20v20H20V20zM0 20h20v20H0V20z' fill='%23FFFFFF' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E')" }}>
              </div>
            </div>
            
            <div className="flex flex-col md:flex-row items-center relative z-10">
              {/* Text Content with Animation */}
              <div className={`md:w-1/2 text-center md:text-left mb-16 md:mb-0 transition-all duration-700 ${isHeroVisible ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-10'}`}>
                <div className="inline-block px-4 py-1.5 text-sm font-semibold bg-blue-600 bg-opacity-30 rounded-full mb-5 border border-blue-400 border-opacity-20 shadow-inner">
                  Trusted by 1,000+ event organizers
                </div>
                
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 leading-tight tracking-tight">
                  Streamline Your <span className="bg-gradient-to-r from-blue-300 to-indigo-300 bg-clip-text text-transparent">Event Check-ins</span>
                </h1>
                
                <p className="text-xl text-blue-50 max-w-2xl mb-10 leading-relaxed">
                  Leave paper lists behind. Our QR Check-in System helps event organizers manage attendees efficiently with digital check-ins and real-time analytics.
                </p>
                
                <div className="flex flex-col sm:flex-row gap-5 justify-center md:justify-start">
                  <Link 
                    to="/register" 
                    className="flex items-center justify-center gap-2 bg-white text-blue-700 px-8 py-4 rounded-xl shadow-lg hover:shadow-xl hover:bg-blue-50 transition-all duration-300 transform hover:-translate-y-1 font-medium"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                    </svg>
                    <span>Get Started Free</span>
                  </Link>
                  
                  <Link 
                    to="/login" 
                    className="flex items-center justify-center gap-2 bg-transparent text-white border-2 border-white px-7 py-3.5 rounded-xl hover:bg-white hover:bg-opacity-10 transition-all duration-300 shadow-md"
                  >
                    <span>Watch Demo</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                    </svg>
                  </Link>
                </div>
                
                {isOffline && (
                  <div className="mt-8 inline-block py-3 px-5 bg-yellow-500 bg-opacity-20 text-yellow-100 rounded-xl border border-yellow-400 border-opacity-40 shadow-lg">
                    <div className="flex items-center space-x-3">
                      <div className="h-3 w-3 rounded-full bg-yellow-300 animate-pulse"></div>
                      <span className="font-medium">You are currently offline. Limited functionality available.</span>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Enhanced Demo/Image with Animation */}
              <div className={`md:w-1/2 transition-all duration-700 delay-300 ${isHeroVisible ? 'opacity-100 translate-x-0 scale-100' : 'opacity-0 translate-x-10 scale-95'}`}>
                <div className="relative">
                  {/* Modern Device Frame */}
                  <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-3xl p-5 shadow-2xl border border-gray-700 transform -rotate-1 hover:rotate-0 transition-all duration-500">
                    <div className="rounded-2xl overflow-hidden bg-white aspect-w-9 aspect-h-16 shadow-inner">
                      {/* App Screenshot with better styling */}
                      <div className="bg-gradient-to-b from-gray-50 to-gray-100 w-full h-full p-4">
                        {/* App Header with gradient */}
                        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-3 rounded-lg flex items-center justify-between mb-4 shadow-md">
                          <div className="font-bold flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                            Event Check-in Pro
                          </div>
                          <div className="h-8 w-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center shadow-sm">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-6-3a2 2 0 11-4 0 2 2 0 014 0zm-2 4a5 5 0 00-4.546 2.916A5.986 5.986 0 0010 16a5.986 5.986 0 004.546-2.084A5 5 0 0010 11z" clipRule="evenodd" />
                            </svg>
                          </div>
                        </div>
                        
                        {/* Enhanced QR Scanner UI */}
                        <div className="bg-gradient-to-b from-gray-900 to-gray-800 rounded-lg p-3 flex items-center justify-center mb-4 relative overflow-hidden shadow-lg">
                          <div className="absolute inset-4 border-2 border-blue-400 border-opacity-50 rounded-md shadow-inner"></div>
                          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-red-500 animate-pulse shadow-lg"></div>
                          <div className="absolute top-0 left-0 right-0 bottom-0 bg-blue-500 bg-opacity-5"></div>
                          <div className="text-white text-sm font-medium text-center mt-16 bg-black bg-opacity-50 px-4 py-1 rounded-full shadow-sm">
                            <div className="flex items-center justify-center">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                              </svg>
                              Scan QR Code
                            </div>
                          </div>
                        </div>
                        
                        {/* Enhanced Attendee List */}
                        <div className="space-y-2">
                          <div className="bg-white p-3 rounded-lg shadow-md flex justify-between items-center hover:shadow-lg transition-shadow border border-gray-100">
                            <div className="flex items-center">
                              <div className="w-9 h-9 bg-gradient-to-br from-green-400 to-emerald-500 text-white rounded-full flex items-center justify-center mr-3 shadow-sm">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                              </div>
                              <div>
                                <div className="text-sm font-medium text-gray-800">Jane Smith</div>
                                <div className="text-xs text-gray-500">VIP Ticket #1234</div>
                              </div>
                            </div>
                            <div className="text-xs text-gray-500 font-medium px-2 py-1 bg-green-50 rounded-full">Just now</div>
                          </div>
                          
                          <div className="bg-white p-3 rounded-lg shadow-md flex justify-between items-center hover:shadow-lg transition-shadow border border-gray-100">
                            <div className="flex items-center">
                              <div className="w-9 h-9 bg-gradient-to-br from-green-400 to-emerald-500 text-white rounded-full flex items-center justify-center mr-3 shadow-sm">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                              </div>
                              <div>
                                <div className="text-sm font-medium text-gray-800">Michael Chen</div>
                                <div className="text-xs text-gray-500">Standard Ticket #5678</div>
                              </div>
                            </div>
                            <div className="text-xs text-gray-500 font-medium px-2 py-1 bg-green-50 rounded-full">3m ago</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Enhanced Stats Popup */}
                  <div className="absolute -right-8 -bottom-8 bg-white rounded-xl shadow-xl p-4 w-48 transform rotate-3 backdrop-blur-md bg-opacity-95 border border-gray-100 hover:scale-105 transition-transform duration-300">
                    <div className="text-sm font-semibold text-gray-800 mb-2 flex items-center">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Real-time Check-ins
                    </div>
                    <div className="h-2.5 bg-gray-100 rounded-full mb-2 overflow-hidden shadow-inner">
                      <div className="h-2.5 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full w-3/4 shadow-lg"></div>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 font-medium">75/100</span>
                      <span className="text-green-600 font-bold">75%</span>
                    </div>
                  </div>
                  
                  {/* Additional decoration elements */}
                  <div className="absolute -left-6 top-1/3 bg-gradient-to-r from-purple-500 to-indigo-500 w-12 h-12 rounded-full blur-lg opacity-30 animate-pulse"></div>
                  <div className="absolute -right-3 top-10 bg-gradient-to-r from-blue-400 to-cyan-400 w-8 h-8 rounded-full blur-md opacity-40"></div>
                </div>
              </div>
            </div>
            
            {/* Enhanced Trust Bar */}
            <div className={`mt-16 transition-all duration-700 delay-500 ${isHeroVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
              <div className="text-sm font-medium uppercase tracking-wider text-center text-blue-200 mb-8">Trusted by companies worldwide</div>
              <div className="flex flex-wrap justify-center gap-10 md:gap-16">
                {/* Placeholder logos with more modern styling */}
                <div className="h-10 w-28 bg-white bg-opacity-10 rounded-lg flex items-center justify-center border border-white border-opacity-20 hover:bg-opacity-20 transition-all cursor-pointer shadow-md backdrop-blur-sm">
                  <div className="h-4 w-16 bg-white opacity-70 rounded"></div>
                </div>
                <div className="h-10 w-28 bg-white bg-opacity-10 rounded-lg flex items-center justify-center border border-white border-opacity-20 hover:bg-opacity-20 transition-all cursor-pointer shadow-md backdrop-blur-sm">
                  <div className="h-4 w-14 bg-white opacity-70 rounded"></div>
                </div>
                <div className="h-10 w-28 bg-white bg-opacity-10 rounded-lg flex items-center justify-center border border-white border-opacity-20 hover:bg-opacity-20 transition-all cursor-pointer shadow-md backdrop-blur-sm">
                  <div className="h-4 w-18 bg-white opacity-70 rounded"></div>
                </div>
                <div className="h-10 w-28 bg-white bg-opacity-10 rounded-lg flex items-center justify-center border border-white border-opacity-20 hover:bg-opacity-20 transition-all cursor-pointer shadow-md backdrop-blur-sm">
                  <div className="h-4 w-12 bg-white opacity-70 rounded"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* How It Works - Only for non-authenticated users */}
      {showMarketingContent && (
        <div className="py-24 bg-white relative overflow-hidden">
          {/* Background shapes for visual interest */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-10 -left-10 w-72 h-72 rounded-full bg-blue-50 opacity-80"></div>
            <div className="absolute -bottom-20 -right-20 w-80 h-80 rounded-full bg-indigo-50 opacity-70"></div>
            <div className="absolute top-1/2 left-1/3 w-40 h-40 rounded-full bg-purple-50 opacity-60"></div>
          </div>
          
          <div className="max-w-6xl mx-auto px-4 relative z-10">
            <div className="text-center mb-20">
              <div className="inline-block px-4 py-1.5 text-sm font-semibold bg-blue-100 text-blue-800 rounded-full mb-5 shadow-sm">
                HOW IT WORKS
              </div>
              <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-5 tracking-tight bg-clip-text bg-gradient-to-r from-blue-800 to-indigo-700 text-transparent">Simple Process, Powerful Results</h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
                Our platform streamlines the entire event management workflow from registration to real-time analytics
              </p>
            </div>
            
            <div className="relative">
              {/* Enhanced Connection Line with animation */}
              <div className="absolute top-24 left-0 right-0 h-1 bg-gradient-to-r from-blue-200 via-indigo-200 to-blue-200 hidden md:block rounded-full shadow-sm">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-400 via-indigo-500 to-blue-400 h-full w-1/2 rounded-full animate-pulse opacity-70"></div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-5 gap-10">
                {howItWorksSteps.map((step, index) => (
                  <div key={index} className="flex flex-col items-center text-center relative group">
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center text-blue-600 mb-8 z-10 shadow-lg border border-blue-200 group-hover:shadow-xl group-hover:scale-110 transition-all duration-300">
                      <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center">
                        {step.icon}
                      </div>
                    </div>
                    
                    <div className="absolute top-10 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-xl font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 w-8 h-8 rounded-full flex items-center justify-center shadow-md hidden md:flex">
                      {index + 1}
                    </div>
                    
                    <h3 className="text-xl font-bold mb-3 text-gray-800 group-hover:text-blue-700 transition-colors">{step.title}</h3>
                    <p className="text-gray-600 leading-relaxed">{step.description}</p>
                    
                    {/* Visual indicator for hover state */}
                    <div className="h-1 w-0 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full mt-4 group-hover:w-20 transition-all duration-300"></div>
                  </div>
                ))}
              </div>
              
              {/* Added visual element - curved arrow pointing to first step */}
              <div className="hidden md:block absolute -top-14 left-10 transform rotate-45">
                <svg width="50" height="50" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="text-blue-500">
                  <path d="M7 13L12 18L17 13M12 18V6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                <div className="text-blue-700 font-medium ml-2 transform -rotate-45">Start Here</div>
              </div>
            </div>
            
            {/* Added call-to-action button */}
            <div className="mt-16 text-center">
              <Link 
                to="/register" 
                className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-xl shadow-lg hover:shadow-xl hover:from-blue-700 hover:to-indigo-700 transform hover:-translate-y-1 transition-all duration-300"
              >
                <span>Ready to streamline your events?</span>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Key Features - Only for non-authenticated users */}
      {showMarketingContent && (
        <div className="py-24 bg-gradient-to-b from-gray-50 to-white relative overflow-hidden">
          {/* Background decoration */}
          <div className="absolute right-0 top-0 h-full w-1/3 bg-gradient-to-l from-blue-50 to-transparent opacity-70"></div>
          <div className="absolute left-0 bottom-0 h-full w-1/4 bg-gradient-to-t from-indigo-50 to-transparent opacity-60"></div>
          
          <div className="max-w-6xl mx-auto px-4 relative z-10">
            <div className="text-center mb-20">
              <div className="inline-block px-4 py-1.5 text-sm font-semibold bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 rounded-full mb-5 shadow-sm border border-blue-200 border-opacity-50">
                POWERFUL FEATURES
              </div>
              <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-5 tracking-tight leading-tight">
                Everything you need to run <br className="hidden md:block" />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">successful events</span>
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                Our comprehensive platform helps you manage the entire event lifecycle from planning to post-event analysis
              </p>
            </div>
            
            {/* Enhanced feature grid with animation on hover */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="group relative"
                  data-aos="fade-up"
                  data-aos-delay={index * 100}
                >
                  <Feature 
                    icon={feature.icon}
                    title={feature.title}
                    description={feature.description}
                    stat={feature.stat}
                    bgColor={`${feature.bgColor} group-hover:bg-gradient-to-br from-white to-${feature.bgColor.split('-')[1]}-100`}
                    iconColor={feature.iconColor}
                    borderColor={`border-transparent group-hover:${feature.borderColor}`}
                  />
                  
                  {/* Subtle animation indicator */}
                  <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-0 h-1 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-full group-hover:w-1/3 transition-all duration-300"></div>
                </div>
              ))}
            </div>
            
            {/* Enhanced Feature Highlight with modern design */}
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 transform transition-all hover:shadow-2xl hover:scale-[1.02] duration-500">
              <div className="flex flex-col lg:flex-row">
                <div className="lg:w-1/2 p-10 lg:p-14">
                  <div className="inline-flex items-center px-4 py-1.5 text-sm font-semibold bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 rounded-full mb-5 border border-blue-200 border-opacity-50">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                    FEATURED TECHNOLOGY
                  </div>
                  
                  <h3 className="text-3xl font-bold mb-5 text-transparent bg-clip-text bg-gradient-to-r from-blue-800 to-indigo-700">QR Code Check-in System</h3>
                  
                  <p className="text-gray-700 mb-8 text-lg leading-relaxed">
                    Our flagship feature streamlines the entire check-in process, allowing you to register attendees in seconds, not minutes. Perfect for conferences, workshops, and large-scale events where efficiency matters.
                  </p>
                  
                  <ul className="space-y-4 mb-10">
                    {[
                      "Scan tickets in under 2 seconds",
                      "Works offline - no internet required",
                      "Automatic attendee notifications",
                      "Multi-device synchronization"
                    ].map((item, i) => (
                      <li key={i} className="flex items-start">
                        <div className="w-6 h-6 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full flex items-center justify-center mr-3 text-white shadow-sm flex-shrink-0">
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                        <span className="text-gray-800">{item}</span>
                      </li>
                    ))}
                  </ul>
                  
                  <Link 
                    to="/register"
                    className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-4 rounded-xl hover:shadow-lg hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 font-medium inline-flex items-center transform hover:-translate-y-1"
                  >
                    <span>Try it yourself</span>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </Link>
                </div>
                
                <div className="lg:w-1/2 bg-gradient-to-br from-blue-900 via-indigo-900 to-gray-900 p-8 flex items-center justify-center overflow-hidden relative">
                  {/* Background decoration */}
                  <div className="absolute inset-0 opacity-10">
                    <div className="absolute top-0 right-0 w-full h-full bg-grid-white bg-opacity-10"></div>
                    <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-blue-500 opacity-20 blur-3xl"></div>
                    <div className="absolute -bottom-20 -left-20 w-64 h-64 rounded-full bg-indigo-500 opacity-20 blur-3xl"></div>
                  </div>
                  
                  <div className="relative w-full max-w-md z-10">
                    {/* Enhanced QR Code Demo */}
                    <div className="bg-white rounded-xl shadow-2xl p-6 transform hover:scale-105 transition-transform duration-500">
                      <div className="flex justify-between items-center mb-6">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white shadow-md mr-3">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                            </svg>
                          </div>
                          <div className="text-lg font-bold text-gray-800">Event Check-in</div>
                        </div>
                        <div className="flex items-center gap-1 bg-green-100 text-green-800 text-xs font-medium px-2.5 py-1 rounded-full">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          <span>Live</span>
                        </div>
                      </div>
                      
                      <div className="bg-gradient-to-b from-gray-900 to-black p-6 rounded-lg flex flex-col items-center mb-6 shadow-inner">
                        {/* Enhanced QR Code */}
                        <div className="w-48 h-48 bg-white p-3 rounded-lg mb-3 shadow-lg">
                          <div className="w-full h-full border-8 border-black grid grid-cols-5 grid-rows-5">
                            {/* Generate pattern for QR code */}
                            <div className="col-span-2 row-span-2 bg-black rounded-lg m-1"></div>
                            <div className="col-span-1 row-span-1 bg-black m-1"></div>
                            <div className="col-span-2 row-span-2 bg-black rounded-lg m-1"></div>
                            <div className="col-span-1 row-span-1 bg-black m-1"></div>
                            <div className="col-span-1 row-span-1 bg-black m-1"></div>
                            <div className="col-span-2 row-span-2 bg-black rounded-lg m-1"></div>
                            <div className="col-span-1 row-span-1 bg-black m-1"></div>
                            <div className="col-span-1 row-span-1 bg-black m-1"></div>
                            <div className="col-span-1 row-span-1 bg-black m-1"></div>
                            <div className="col-span-1 row-span-1 bg-black m-1"></div>
                            <div className="col-span-1 row-span-1 bg-black m-1"></div>
                          </div>
                        </div>
                        <div className="text-white text-sm font-medium px-4 py-1.5 bg-blue-600 rounded-full shadow-md flex items-center">
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                          </svg>
                          Scan to check in
                        </div>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <div className="flex items-center">
                            <div className="w-10 h-10 bg-gradient-to-br from-green-400 to-emerald-500 text-white rounded-full flex items-center justify-center mr-3 shadow-md">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                            </div>
                            <div>
                              <div className="text-sm font-semibold text-gray-900">Michael Johnson</div>
                              <div className="text-xs text-gray-500">VIP Ticket #A1234</div>
                            </div>
                          </div>
                          <div className="bg-green-100 text-green-800 text-xs px-2.5 py-1.5 rounded-full flex items-center shadow-sm">
                            <div className="w-1.5 h-1.5 bg-green-600 rounded-full mr-1.5"></div>
                            Checked in
                          </div>
                        </div>
                        
                        <div className="w-full h-px bg-gradient-to-r from-transparent via-gray-200 to-transparent"></div>
                        
                        <div className="bg-gray-50 rounded-lg p-3 shadow-sm">
                          <div className="font-medium mb-2 text-gray-900 flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Event Information:
                          </div>
                          <div className="grid grid-cols-2 gap-1.5 text-sm">
                            <div className="text-gray-500">Date:</div>
                            <div className="font-medium text-gray-800">April 15, 2025</div>
                            <div className="text-gray-500">Time:</div>
                            <div className="font-medium text-gray-800">10:00 AM</div>
                            <div className="text-gray-500">Location:</div>
                            <div className="font-medium text-gray-800">Main Conference Room</div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* Enhanced Animation overlay */}
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-2/3 h-12 bg-green-500 bg-opacity-20 rounded-full flex items-center justify-center border border-green-500 animate-pulse shadow-lg">
                      <div className="text-white font-semibold flex items-center">
                        <div className="w-3 h-3 bg-green-500 rounded-full mr-2 animate-ping"></div>
                        Scanning...
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Testimonials - Only for non-authenticated users */}
      {showMarketingContent && (
        <div className="py-24 bg-gray-50 relative overflow-hidden">
          {/* Background decoration */}
          <div className="absolute top-0 left-0 right-0 h-1/3 bg-gradient-to-b from-white to-transparent"></div>
          <div className="absolute bottom-0 left-0 right-0 h-1/3 bg-gradient-to-t from-white to-transparent"></div>
          <div className="absolute inset-0">
            <div className="absolute top-1/4 right-1/4 w-64 h-64 rounded-full bg-blue-100 opacity-40 blur-3xl"></div>
            <div className="absolute bottom-1/4 left-1/4 w-80 h-80 rounded-full bg-indigo-100 opacity-40 blur-3xl"></div>
          </div>
          
          <div className="max-w-6xl mx-auto px-4 relative z-10">
            <div className="text-center mb-16">
              <div className="inline-block px-4 py-1.5 text-sm font-semibold bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 rounded-full mb-5 shadow-sm border border-blue-200 border-opacity-50">
                TESTIMONIALS
              </div>
              <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-5 tracking-tight">
                Trusted by <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Event Professionals</span>
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                See what leading event organizers have accomplished with our platform
              </p>
            </div>
            
            {/* Enhanced Featured Testimonial Carousel */}
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden mb-20 border border-gray-100 transform transition-all hover:shadow-2xl duration-500">
              <div className="flex flex-col lg:flex-row">
                <div className="lg:w-1/2 p-10 lg:p-14 relative">
                  {/* Enhanced decorative elements */}
                  <div className="absolute top-8 left-8 text-8xl text-blue-200 opacity-30 font-serif">"</div>
                  
                  <div className="relative z-10">
                    {testimonials.map((testimonial, index) => (
                      <div 
                        key={index} 
                        className={`transition-all duration-700 ${index === activeTestimonial ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10 absolute inset-0'}`}
                      >
                        <p className="text-lg md:text-2xl text-gray-700 mb-10 relative z-10 leading-relaxed font-medium">
                          "{testimonial.quote}"
                        </p>
                        
                        <div className="flex items-center mb-8">
                          <div className="w-16 h-16 rounded-full overflow-hidden mr-4 border-2 border-blue-100 p-0.5 shadow-md">
                            <div className="w-full h-full bg-gradient-to-br from-blue-400 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xl">
                              {testimonial.author.split(' ').map(name => name[0]).join('')}
                            </div>
                          </div>
                          <div>
                            <div className="font-bold text-gray-900 text-lg">{testimonial.author}</div>
                            <div className="text-gray-600">{testimonial.role}</div>
                            <div className="text-blue-600 font-medium">{testimonial.company}</div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-5">
                          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 text-center shadow-sm border border-blue-100">
                            <div className="text-xl font-bold text-blue-700">{testimonial.metrics?.attendees}</div>
                            <div className="text-sm text-gray-600">Attendees</div>
                          </div>
                          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 text-center shadow-sm border border-blue-100">
                            <div className="text-xl font-bold text-blue-700">{testimonial.metrics?.timeSaved}</div>
                            <div className="text-sm text-gray-600">Time Saved</div>
                          </div>
                          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 text-center shadow-sm border border-blue-100">
                            <div className="text-xl font-bold text-blue-700">{testimonial.metrics?.satisfaction}</div>
                            <div className="text-sm text-gray-600">Satisfaction</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  {/* Enhanced Navigation Controls */}
                  <div className="flex justify-center space-x-3 mt-12">
                    {testimonials.map((_, index) => (
                      <button 
                        key={index}
                        onClick={() => setActiveTestimonial(index)}
                        className={`w-12 h-2 rounded-full transition-all duration-300 ${
                          index === activeTestimonial 
                            ? 'bg-gradient-to-r from-blue-600 to-indigo-600 w-16' 
                            : 'bg-gray-200 hover:bg-gray-300'
                        }`}
                        aria-label={`View testimonial ${index + 1}`}
                      ></button>
                    ))}
                  </div>
                </div>
                
                <div className="lg:w-1/2 bg-gradient-to-br from-blue-600 to-indigo-700 p-10 lg:p-14 flex items-center justify-center relative overflow-hidden">
                  {/* Background decoration */}
                  <div className="absolute inset-0 opacity-20">
                    <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full bg-white blur-3xl"></div>
                    <div className="absolute -bottom-20 -left-20 w-80 h-80 rounded-full bg-blue-300 blur-3xl"></div>
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-full h-full"
                         style={{
                           backgroundImage: "url('data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23FFFFFF' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')"
                         }}>
                    </div>
                  </div>
                  
                  <div className="relative max-w-md z-10 transform transition-all duration-700 hover:scale-105">
                    {/* Enhanced Case Study Preview */}
                    <div className="bg-white rounded-xl shadow-2xl overflow-hidden">
                      <div className="bg-gray-50 px-6 py-4 border-b border-gray-100">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <div className="font-bold text-gray-800">Case Study</div>
                          </div>
                          <div className="p-1.5 bg-white rounded-md shadow-sm">
                            <div className="bg-gray-200 h-5 w-16 rounded"></div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="p-6">
                        <h3 className="text-xl font-bold text-gray-800 mb-4">
                          How {testimonials[activeTestimonial].company} Transformed Their Event Check-ins
                        </h3>
                        
                        <div className="flex items-center mb-4">
                          <div className="flex text-yellow-400 mr-2">
                            {[...Array(5)].map((_, i) => (
                              <svg key={i} xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                              </svg>
                            ))}
                          </div>
                          <div className="text-gray-600 font-medium">Success story</div>
                        </div>
                        
                        {/* Enhanced case study preview content */}
                        <div className="space-y-3 mb-6">
                          <div className="flex items-start">
                            <div className="w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center mt-0.5 mr-2 flex-shrink-0">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <p className="text-sm text-gray-600">Registration time reduced by 70%</p>
                          </div>
                          <div className="flex items-start">
                            <div className="w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center mt-0.5 mr-2 flex-shrink-0">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <p className="text-sm text-gray-600">Eliminated long check-in lines completely</p>
                          </div>
                          <div className="flex items-start">
                            <div className="w-5 h-5 rounded-full bg-green-100 text-green-600 flex items-center justify-center mt-0.5 mr-2 flex-shrink-0">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <p className="text-sm text-gray-600">Real-time analytics improved event management</p>
                          </div>
                        </div>
                        
                        <div className="border-t border-gray-100 pt-5">
                          <button className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-2 px-4 rounded-lg text-sm font-medium hover:from-blue-700 hover:to-indigo-700 transition-all shadow-sm flex items-center w-full justify-center">
                            Read the full case study
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1.5" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Enhanced Testimonials Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {testimonials.map((testimonial, index) => (
                <div key={index} className="transform transition-all duration-300 hover:-translate-y-2">
                  <Testimonial 
                    quote={testimonial.quote}
                    author={testimonial.author}
                    role={testimonial.role}
                    company={testimonial.company}
                    logo={testimonial.logo}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* FAQ Section - Only for non-authenticated users */}
      {showMarketingContent && (
        <div className="py-24 bg-white relative overflow-hidden">
          {/* Background decoration */}
          <div className="absolute top-0 -right-20 h-96 w-96 rounded-full bg-blue-50 opacity-50 blur-3xl"></div>
          <div className="absolute bottom-0 -left-20 h-96 w-96 rounded-full bg-indigo-50 opacity-50 blur-3xl"></div>
          
          <div className="max-w-4xl mx-auto px-4 relative z-10">
            <div className="text-center mb-16">
              <div className="inline-block px-4 py-1.5 text-sm font-semibold bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-800 rounded-full mb-5 shadow-sm border border-blue-200 border-opacity-50">
                FAQ
              </div>
              <h2 className="text-3xl md:text-5xl font-bold text-gray-900 mb-5 tracking-tight">
                Frequently Asked <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Questions</span>
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
                Everything you need to know about our event check-in system
              </p>
            </div>
            
            <div className="space-y-6">
              {faqItems.map((item, index) => (
                <div 
                  key={index} 
                  className="bg-white rounded-xl p-7 shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 border border-gray-100 group"
                >
                  <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center group-hover:text-blue-700 transition-colors">
                    <span className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex items-center justify-center text-sm mr-3 flex-shrink-0 shadow-md">
                      {index + 1}
                    </span>
                    {item.question}
                  </h3>
                  <p className="text-gray-600 leading-relaxed pl-11">
                    {item.answer}
                  </p>
                </div>
              ))}
            </div>
            
            {/* Added contact button */}
            <div className="mt-12 text-center">
              <div className="inline-flex items-center bg-blue-50 text-blue-800 px-6 py-3 rounded-lg shadow-sm border border-blue-100">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Have more questions? <Link to="/contact" className="font-semibold underline ml-1">Contact our team</Link></span>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Footer CTA - Only for non-authenticated users */}
      {showMarketingContent && (
        <div className="py-24 bg-gradient-to-br from-blue-700 via-indigo-700 to-purple-800 relative overflow-hidden">
          {/* Background decoration */}
          <div className="absolute inset-0">
            <div className="absolute top-0 left-0 right-0 bottom-0 opacity-10"
                 style={{
                   backgroundImage: "url('data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23FFFFFF' fill-opacity='0.15'%3E%3Cpath d='M50 50c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10c0 5.523-4.477 10-10 10s-10-4.477-10-10 4.477-10 10-10zM10 10c0-5.523 4.477-10 10-10s10 4.477 10 10-4.477 10-10 10c0 5.523-4.477 10-10 10S0 25.523 0 20s4.477-10 10-10zm10 8c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8zm40 40c4.418 0 8-3.582 8-8s-3.582-8-8-8-8 3.582-8 8 3.582 8 8 8z' /%3E%3C/g%3E%3C/g%3E%3C/svg%3E')"
                 }}>
            </div>
            <div className="absolute -top-20 -right-20 w-96 h-96 rounded-full bg-blue-500 opacity-20 blur-3xl"></div>
            <div className="absolute -bottom-20 -left-20 w-96 h-96 rounded-full bg-purple-500 opacity-20 blur-3xl"></div>
          </div>
          
          <div className="max-w-6xl mx-auto px-4 text-center relative z-10">
            <div className="inline-flex items-center bg-white bg-opacity-10 rounded-full px-6 py-2 mb-8 border border-white border-opacity-20 backdrop-blur-sm">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse mr-2"></div>
              <span className="text-green-100 text-sm font-medium">Trusted by 1,000+ organizations worldwide</span>
            </div>
            
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-8 leading-tight">
              Ready to Transform Your <br className="hidden md:block" />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-200 to-indigo-100">Event Check-ins?</span>
            </h2>
            
            <p className="text-white text-xl opacity-90 mb-10 max-w-2xl mx-auto leading-relaxed">
              Join thousands of event organizers who have simplified their check-in process and improved their attendee experience.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-6 justify-center">
              <Link 
                to="/register" 
                className="bg-white text-blue-700 px-8 py-4 rounded-xl font-medium hover:bg-blue-50 transition-all duration-300 transform hover:-translate-y-1 shadow-lg flex items-center justify-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>Get Started Free</span>
              </Link>
              
              <Link 
                to="/contact" 
                className="bg-transparent text-white border-2 border-white px-8 py-4 rounded-xl font-medium hover:bg-white hover:text-blue-700 transition-all duration-300 flex items-center justify-center"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <span>Contact Us</span>
              </Link>
            </div>
            
            <div className="mt-10 inline-flex items-center justify-center bg-blue-800 bg-opacity-30 rounded-full px-6 py-3 text-blue-100 text-sm border border-blue-700">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Get started today • No commitments • Easy setup</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}