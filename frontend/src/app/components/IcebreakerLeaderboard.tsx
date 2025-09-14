import React, { useState, useEffect } from 'react';
import {
  Trophy,
  Medal,
  Award,
  Crown,
  Star,
  TrendingUp,
  Zap,
  Target,
  Clock,
  Heart,
  Gift
} from 'lucide-react';

interface LeaderboardEntry {
  rank: number;
  user: {
    id: string | number;  // Support both guest (string) and regular user (number) IDs
    username: string;
    full_name: string;
    first_name: string;
    last_name: string;
  };
  total_points: number;
  base_points: number;
  bonus_points: number;
  activities_completed: number;
  current_streak: number;
  longest_streak: number;
  likes_received: number;
  lucky_bonus_count: number;
  average_response_time: number;
}

interface UserStats {
  rank: number;
  total_points: number;
  base_points: number;
  bonus_points: number;
  activities_completed: number;
  current_streak: number;
  longest_streak: number;
  likes_received: number;
  likes_given: number;
  lucky_bonus_count: number;
  total_lucky_points: number;
  average_response_time: number;
  streak_multiplier: number;
}

interface IcebreakerLeaderboardProps {
  eventId: string;
}

const IcebreakerLeaderboard: React.FC<IcebreakerLeaderboardProps> = ({ eventId }) => {
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'leaderboard' | 'mystats'>('leaderboard');
  const [totalParticipants, setTotalParticipants] = useState(0);

  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchLeaderboardData();
    fetchUserStats();
  }, [eventId]);

  const fetchLeaderboardData = async () => {
    try {
      console.log('Fetching leaderboard for event:', eventId);
      const token = localStorage.getItem('auth_token');
      const response = await fetch(
        `${API_BASE}/api/communication/icebreakers/leaderboard/?event_id=${eventId}`,
        {
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('Leaderboard response status:', response.status);
      if (response.ok) {
        const data = await response.json();
        console.log('Leaderboard data:', data);
        console.log('Leaderboard array:', data.leaderboard);
        console.log('Total participants:', data.total_participants);
        setLeaderboard(data.leaderboard || []);
        setTotalParticipants(data.total_participants || 0);
        console.log('State set - leaderboard length:', data.leaderboard?.length);
      } else {
        console.error('Leaderboard fetch failed:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  const fetchUserStats = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      const response = await fetch(
        `${API_BASE}/api/communication/icebreakers/user_stats/?event_id=${eventId}`,
        {
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setUserStats(data);
      }
    } catch (error) {
      console.error('Error fetching user stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankIcon = (rank: number) => {
    switch (rank) {
      case 1:
        return <Crown className="w-6 h-6 text-yellow-500" />;
      case 2:
        return <Medal className="w-6 h-6 text-gray-400" />;
      case 3:
        return <Award className="w-6 h-6 text-amber-600" />;
      default:
        return <Trophy className="w-5 h-5 text-gray-500" />;
    }
  };

  const getRankBadgeColor = (rank: number) => {
    switch (rank) {
      case 1:
        return 'bg-gradient-to-r from-yellow-400 to-yellow-600 text-white';
      case 2:
        return 'bg-gradient-to-r from-gray-300 to-gray-500 text-white';
      case 3:
        return 'bg-gradient-to-r from-amber-400 to-amber-600 text-white';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex">
          <button
            onClick={() => setActiveTab('leaderboard')}
            className={`flex-1 px-4 py-3 text-sm font-medium ${
              activeTab === 'leaderboard'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Trophy className="w-4 h-4 inline-block mr-2" />
            Leaderboard
          </button>
          <button
            onClick={() => setActiveTab('mystats')}
            className={`flex-1 px-4 py-3 text-sm font-medium ${
              activeTab === 'mystats'
                ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Star className="w-4 h-4 inline-block mr-2" />
            My Stats
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'leaderboard' ? (
          <div>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                <div className="bg-gradient-to-r from-yellow-400 to-orange-500 p-3 rounded-full mr-2">
                  <Trophy className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">
                    🏆 Icebreaker Champions
                  </h3>
                  <p className="text-sm text-gray-600">
                    Top performers in icebreaker activities
                  </p>
                </div>
              </div>
              <div className="text-center">
                <div className="bg-blue-100 text-blue-800 px-3 py-2 rounded-full">
                  <div className="text-lg font-bold">{totalParticipants}</div>
                  <div className="text-xs">participants</div>
                </div>
              </div>
            </div>

            {leaderboard.length === 0 ? (
              <div className="text-center py-8">
                <Trophy className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                <p className="text-gray-500">No participants yet</p>
                <p className="text-gray-400 text-sm">Be the first to participate!</p>
              </div>
            ) : (
              <div className="space-y-3">
                {leaderboard.map((entry) => (
                  <div
                    key={entry.user.id}
                    className="flex items-center py-4 border-b border-gray-100 last:border-b-0"
                  >
                    {/* Rank */}
                    <div className="flex items-center mr-4">
                      <div
                        className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${getRankBadgeColor(
                          entry.rank
                        )}`}
                      >
                        {entry.rank <= 3 ? getRankIcon(entry.rank) : entry.rank}
                      </div>
                    </div>

                    {/* User Info */}
                    <div className="flex-1 min-w-0">
                      <div className="mb-2">
                        <div className="flex items-center">
                          <p className="text-xl font-bold text-gray-900">
                            {entry.user.full_name || entry.user.username}
                          </p>
                          {entry.rank <= 3 && (
                            <span className="ml-2 text-sm text-yellow-600 font-medium">
                              🏆 Champion
                            </span>
                          )}
                        </div>
                        <div className="flex items-center mt-2 space-x-2">
                          {entry.current_streak >= 3 && (
                            <div className="flex items-center bg-gradient-to-r from-orange-100 to-yellow-100 text-orange-700 px-3 py-1 rounded-full border border-orange-200">
                              <Zap className="w-4 h-4" />
                              <span className="text-xs font-bold ml-1">
                                {entry.current_streak} Day Streak!
                              </span>
                            </div>
                          )}
                          {entry.lucky_bonus_count > 0 && (
                            <div className="flex items-center bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700 px-3 py-1 rounded-full border border-purple-200">
                              <Gift className="w-4 h-4" />
                              <span className="text-xs font-bold ml-1">
                                Lucky x{entry.lucky_bonus_count}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-6 text-sm text-gray-600">
                        <div className="flex flex-col">
                          <div className="flex items-center">
                            <Target className="w-4 h-4 text-blue-600 mr-1.5" />
                            <span className="font-semibold text-gray-900">{entry.activities_completed}</span>
                            <span className="ml-1">activities</span>
                          </div>
                          <div className="text-xs text-gray-500 mt-0.5">
                            Base: {entry.base_points} | Bonus: {entry.bonus_points}
                          </div>
                          <div className="flex items-center mt-1">
                            <Heart className="w-4 h-4 text-red-600 mr-1.5" />
                            <span className="font-semibold text-gray-900">{entry.likes_received}</span>
                            <span className="ml-1">likes</span>
                          </div>
                        </div>
                        {entry.average_response_time > 0 && (
                          <div className="flex items-center">
                            <Clock className="w-4 h-4 text-green-600 mr-1.5" />
                            <span className="font-semibold text-gray-900">{formatTime(entry.average_response_time)}</span>
                            <span className="ml-1">avg</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Points Display */}
                    <div className="text-right">
                      <div className="text-3xl font-bold text-gray-900">
                        {entry.total_points.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-500">
                        points
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Your Performance
              </h3>
              {userStats ? (
                <>
                  {/* Rank Card */}
                  <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white mb-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-3xl font-bold">
                          #{userStats.rank}
                        </div>
                        <div className="text-blue-100">Your Rank</div>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold">
                          {userStats.total_points.toLocaleString()}
                        </div>
                        <div className="text-blue-100">Total Points</div>
                      </div>
                    </div>
                  </div>

                  {/* Stats Overview */}
                  <div className="bg-white rounded-lg p-6 border border-gray-200 mb-6">
                    <div className="grid grid-cols-3 gap-6">
                      {/* Activities */}
                      <div className="text-center">
                        <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mx-auto mb-3">
                          <Target className="w-6 h-6 text-blue-600" />
                        </div>
                        <div className="text-2xl font-bold text-gray-900">{userStats.activities_completed}</div>
                        <div className="text-sm text-gray-600 mb-2">Activities</div>
                        <div className="text-xs text-gray-500">
                          Best streak: {userStats.longest_streak}
                        </div>
                      </div>

                      {/* Points */}
                      <div className="text-center">
                        <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-full mx-auto mb-3">
                          <Award className="w-6 h-6 text-green-600" />
                        </div>
                        <div className="text-2xl font-bold text-gray-900">{userStats.total_points}</div>
                        <div className="text-sm text-gray-600 mb-2">Total Points</div>
                        <div className="text-xs text-gray-500">
                          Base: {userStats.base_points} + Bonus: {userStats.bonus_points}
                        </div>
                      </div>

                      {/* Social */}
                      <div className="text-center">
                        <div className="flex items-center justify-center w-12 h-12 bg-red-100 rounded-full mx-auto mb-3">
                          <Heart className="w-6 h-6 text-red-600" />
                        </div>
                        <div className="text-2xl font-bold text-gray-900">{userStats.likes_received}</div>
                        <div className="text-sm text-gray-600 mb-2">Likes Received</div>
                        <div className="text-xs text-gray-500">
                          Given: {userStats.likes_given} | Lucky: {userStats.lucky_bonus_count}
                        </div>
                      </div>
                    </div>

                    {/* Additional Stats Bar */}
                    <div className="mt-6 pt-4 border-t border-gray-100">
                      <div className="flex items-start justify-between text-sm">
                        <div className="flex flex-col">
                          <div className="flex items-center mb-1">
                            <Zap className="w-4 h-4 text-orange-500 mr-2" />
                            <span className="text-gray-600">Streak:</span>
                            <span className="ml-2 font-medium">{userStats.current_streak} days</span>
                          </div>
                          <div className="flex items-center">
                            <Gift className="w-4 h-4 text-purple-500 mr-2" />
                            <span className="text-gray-600">Lucky Pts:</span>
                            <span className="ml-2 font-medium text-purple-600">+{userStats.total_lucky_points}</span>
                          </div>
                        </div>
                        <div className="flex items-center">
                          <span className="text-gray-600">Multiplier:</span>
                          <span className="ml-2 font-medium text-orange-600">
                            {userStats.streak_multiplier ? userStats.streak_multiplier.toFixed(1) : '1.0'}x
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Point Breakdown */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-3">Point Breakdown</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Base Points:</span>
                        <span className="font-medium">{userStats.base_points}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Bonus Points:</span>
                        <span className="font-medium text-green-600">+{userStats.bonus_points}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Streak Multiplier:</span>
                        <span className="font-medium text-orange-600">
                          {userStats.streak_multiplier ? userStats.streak_multiplier.toFixed(1) : '1.0'}x
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Lucky Bonuses:</span>
                        <span className="font-medium text-purple-600">
                          +{userStats.total_lucky_points}
                        </span>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <TrendingUp className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">No stats yet</p>
                  <p className="text-gray-400 text-sm">
                    Participate in activities to see your stats!
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IcebreakerLeaderboard;