import { useContext, ReactNode } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';

interface ProtectedRouteProps {
  redirectPath?: string;
  children?: ReactNode;
}

export default function ProtectedRoute({ redirectPath = '/login', children }: ProtectedRouteProps) {
  const { isAuthenticated } = useContext(AuthContext);
  
  if (!isAuthenticated) {
    return <Navigate to={redirectPath} replace />;
  }
  
  // If children are provided, render them; otherwise use Outlet for route-based rendering
  return children ? <>{children}</> : <Outlet />;
}