import { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { User, Mail, Lock, AlertCircle, Loader2, UserPlus } from 'lucide-react';

interface RegisterFormProps {
  onRegisterSuccess: (userData: any, token: string) => void;
}

export default function RegisterForm({ onRegisterSuccess }: RegisterFormProps) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{[key: string]: string}>({});

  // Pre-fill email from URL parameters
  useEffect(() => {
    const emailParam = searchParams.get('email');
    if (emailParam) {
      setFormData(prev => ({ ...prev, email: emailParam }));
    }
  }, [searchParams]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear field error when user types
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const newErrors = {...prev};
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset errors
    setError(null);
    setFieldErrors({});
    
    // Basic validation
    if (formData.password !== formData.password2) {
      setFieldErrors({password2: "Passwords don't match"});
      return;
    }
    
    try {
      setIsSubmitting(true);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/auth/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        if (data.username || data.email || data.password) {
          // Field validation errors
          setFieldErrors({
            ...data.username && { username: data.username.join(' ') },
            ...data.email && { email: data.email.join(' ') },
            ...data.password && { password: data.password.join(' ') },
          });
          throw new Error('Please fix the errors in the form');
        } else {
          throw new Error(data.error || 'Registration failed');
        }
      }
      
      // Registration successful
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('user_data', JSON.stringify(data.user));
      
      // Call the success handler
      onRegisterSuccess(data.user, data.token);

      // Check if there's an event parameter to redirect to communication page
      const eventParam = searchParams.get('event');
      if (eventParam) {
        // Redirect to the event communication page
        navigate(`/events/${eventParam}/communication`);
      } else {
        // Redirect to home page
        navigate('/');
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-lg w-full mx-auto p-8 bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl border border-gray-200">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Create an Account</h2>
        <p className="text-gray-600 mt-2">Join us to create and manage your events</p>
      </div>
      
      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">Username*</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User size={18} className="text-gray-400" />
              </div>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formData.username}
                onChange={handleChange}
                className={`pl-10 w-full px-4 py-2.5 border ${fieldErrors.username ? 'border-red-500' : 'border-gray-300'} rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:outline-none focus:border-indigo-500 text-gray-900`}
                placeholder="Choose a username"
              />
            </div>
            {fieldErrors.username && (
              <p className="mt-1 text-sm text-red-600">{fieldErrors.username}</p>
            )}
          </div>
          
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email*</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail size={18} className="text-gray-400" />
              </div>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleChange}
                className={`pl-10 w-full px-4 py-2.5 border ${fieldErrors.email ? 'border-red-500' : 'border-gray-300'} rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:outline-none focus:border-indigo-500 text-gray-900`}
                placeholder="your@email.com"
              />
            </div>
            {fieldErrors.email && (
              <p className="mt-1 text-sm text-red-600">{fieldErrors.email}</p>
            )}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
            <div className="relative">
              <input
                id="first_name"
                name="first_name"
                type="text"
                value={formData.first_name}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:outline-none focus:border-indigo-500 text-gray-900"
                placeholder="John"
              />
            </div>
          </div>
          
          <div>
            <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
            <div className="relative">
              <input
                id="last_name"
                name="last_name"
                type="text"
                value={formData.last_name}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:outline-none focus:border-indigo-500 text-gray-900"
                placeholder="Doe"
              />
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">Password*</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock size={18} className="text-gray-400" />
              </div>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formData.password}
                onChange={handleChange}
                className={`pl-10 w-full px-4 py-2.5 border ${fieldErrors.password ? 'border-red-500' : 'border-gray-300'} rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:outline-none focus:border-indigo-500 text-gray-900`}
                placeholder="Create a password"
              />
            </div>
            {fieldErrors.password && (
              <p className="mt-1 text-sm text-red-600">{fieldErrors.password}</p>
            )}
          </div>
          
          <div>
            <label htmlFor="password2" className="block text-sm font-medium text-gray-700 mb-1">Confirm Password*</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock size={18} className="text-gray-400" />
              </div>
              <input
                id="password2"
                name="password2"
                type="password"
                required
                value={formData.password2}
                onChange={handleChange}
                className={`pl-10 w-full px-4 py-2.5 border ${fieldErrors.password2 ? 'border-red-500' : 'border-gray-300'} rounded-lg shadow-sm focus:ring-2 focus:ring-indigo-500/20 focus:outline-none focus:border-indigo-500 text-gray-900`}
                placeholder="Confirm your password"
              />
            </div>
            {fieldErrors.password2 && (
              <p className="mt-1 text-sm text-red-600">{fieldErrors.password2}</p>
            )}
          </div>
        </div>
        
        <div className="pt-4">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 border border-transparent rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            {isSubmitting ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Creating account...</span>
              </>
            ) : (
              <>
                <UserPlus size={18} />
                <span>Create Account</span>
              </>
            )}
          </button>
        </div>
      </form>
      
      <div className="mt-8 text-center">
        <p className="text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-indigo-600 hover:text-indigo-500">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}