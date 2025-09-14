import React, { useState } from 'react';
import {
  Heart,
  MessageSquare,
  Trophy,
  Zap,
  Gift,
  Clock,
  ThumbsUp,
  Laugh,
  Flame,
  Brain,
  Sparkles
} from 'lucide-react';

interface IcebreakerResponse {
  id: string;
  user_name: string;
  response_data: any;
  points_earned: number;
  base_points: number;
  speed_bonus: number;
  quality_bonus: number;
  social_bonus: number;
  streak_multiplier: number;
  lucky_multiplier: number;
  like_count: number;
  reply_count: number;
  time_ago: string;
  response_time_seconds?: number;
}

interface IcebreakerResponseCardProps {
  response: IcebreakerResponse;
  activityType: string;
  onReact?: (responseId: string, reactionType: string) => void;
}

const IcebreakerResponseCard: React.FC<IcebreakerResponseCardProps> = ({
  response,
  activityType,
  onReact
}) => {
  const [showPointsBreakdown, setShowPointsBreakdown] = useState(false);
  const [isReacting, setIsReacting] = useState(false);

  const reactionTypes = [
    { type: 'like', icon: ThumbsUp, color: 'text-blue-500', emoji: '👍' },
    { type: 'love', icon: Heart, color: 'text-red-500', emoji: '❤️' },
    { type: 'laugh', icon: Laugh, color: 'text-yellow-500', emoji: '😂' },
    { type: 'wow', icon: Sparkles, color: 'text-purple-500', emoji: '😲' },
    { type: 'think', icon: Brain, color: 'text-green-500', emoji: '🤔' },
    { type: 'fire', icon: Flame, color: 'text-orange-500', emoji: '🔥' },
  ];

  const handleReact = async (reactionType: string) => {
    if (!onReact || isReacting) return;

    setIsReacting(true);
    try {
      await onReact(response.id, reactionType);
    } finally {
      setIsReacting(false);
    }
  };

  const renderResponseContent = () => {
    switch (activityType) {
      case 'poll':
      case 'quiz':
        return (
          <div className="text-gray-800">
            <span className="font-medium">Selected:</span>{' '}
            {response.response_data.selected_option}
          </div>
        );
      case 'question':
      case 'challenge':
      case 'introduction':
        return (
          <div className="text-gray-800">
            {response.response_data.text}
          </div>
        );
      default:
        return (
          <div className="text-gray-500">
            Response content
          </div>
        );
    }
  };

  const getPointsBadges = () => {
    const badges = [];

    if (response.speed_bonus > 0) {
      badges.push(
        <span key="speed" className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 mr-1">
          <Zap className="w-3 h-3 mr-1" />
          Speed +{response.speed_bonus}
        </span>
      );
    }

    if (response.quality_bonus > 0) {
      badges.push(
        <span key="quality" className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-1">
          <Trophy className="w-3 h-3 mr-1" />
          Quality +{response.quality_bonus}
        </span>
      );
    }

    if (response.social_bonus > 0) {
      badges.push(
        <span key="social" className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-pink-100 text-pink-800 mr-1">
          <Heart className="w-3 h-3 mr-1" />
          Social +{response.social_bonus}
        </span>
      );
    }

    if (response.streak_multiplier > 1) {
      badges.push(
        <span key="streak" className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800 mr-1">
          <Zap className="w-3 h-3 mr-1" />
          {response.streak_multiplier.toFixed(1)}x Streak
        </span>
      );
    }

    if (response.lucky_multiplier > 1) {
      badges.push(
        <span key="lucky" className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 mr-1">
          <Gift className="w-3 h-3 mr-1" />
          {response.lucky_multiplier.toFixed(1)}x Lucky!
        </span>
      );
    }

    return badges;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="font-medium text-gray-900">
            {response.user_name}
          </div>
          {response.response_time_seconds && response.response_time_seconds < 600 && (
            <div className="flex items-center text-green-600">
              <Clock className="w-3 h-3 mr-1" />
              <span className="text-xs">
                {Math.round(response.response_time_seconds)}s
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowPointsBreakdown(!showPointsBreakdown)}
            className="flex items-center space-x-1 px-2 py-1 bg-blue-100 hover:bg-blue-200 rounded-lg text-sm font-medium text-blue-800 transition-colors"
          >
            <Trophy className="w-4 h-4" />
            <span>{response.points_earned}</span>
          </button>
          <span className="text-xs text-gray-500">
            {response.time_ago}
          </span>
        </div>
      </div>

      {/* Response Content */}
      <div className="mb-4">
        {renderResponseContent()}
      </div>

      {/* Points Breakdown */}
      {showPointsBreakdown && (
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Points Breakdown</h4>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-600">Base Points:</span>
              <span className="font-medium">{response.base_points}</span>
            </div>
            {response.speed_bonus > 0 && (
              <div className="flex justify-between text-green-600">
                <span>Speed Bonus:</span>
                <span className="font-medium">+{response.speed_bonus}</span>
              </div>
            )}
            {response.quality_bonus > 0 && (
              <div className="flex justify-between text-blue-600">
                <span>Quality Bonus:</span>
                <span className="font-medium">+{response.quality_bonus}</span>
              </div>
            )}
            {response.social_bonus > 0 && (
              <div className="flex justify-between text-pink-600">
                <span>Social Bonus:</span>
                <span className="font-medium">+{response.social_bonus}</span>
              </div>
            )}
            {response.streak_multiplier > 1 && (
              <div className="flex justify-between text-orange-600">
                <span>Streak Multiplier:</span>
                <span className="font-medium">{response.streak_multiplier.toFixed(1)}x</span>
              </div>
            )}
            {response.lucky_multiplier > 1 && (
              <div className="flex justify-between text-purple-600">
                <span>Lucky Multiplier:</span>
                <span className="font-medium">{response.lucky_multiplier.toFixed(1)}x</span>
              </div>
            )}
            <div className="flex justify-between border-t border-gray-200 pt-1">
              <span className="font-medium text-gray-900">Total:</span>
              <span className="font-bold text-blue-600">{response.points_earned}</span>
            </div>
          </div>
        </div>
      )}

      {/* Point Badges */}
      <div className="mb-3">
        {getPointsBadges()}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Reaction buttons */}
          <div className="flex items-center space-x-1">
            {reactionTypes.slice(0, 3).map((reaction) => {
              const Icon = reaction.icon;
              return (
                <button
                  key={reaction.type}
                  onClick={() => handleReact(reaction.type)}
                  disabled={isReacting}
                  className={`flex items-center space-x-1 px-2 py-1 rounded-lg text-xs font-medium transition-colors ${
                    isReacting
                      ? 'opacity-50 cursor-not-allowed'
                      : `hover:bg-gray-100 ${reaction.color}`
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </button>
              );
            })}
            {response.like_count > 0 && (
              <span className="text-xs text-gray-500 ml-2">
                {response.like_count}
              </span>
            )}
          </div>

          {response.reply_count > 0 && (
            <div className="flex items-center space-x-1 text-xs text-gray-500">
              <MessageSquare className="w-4 h-4" />
              <span>{response.reply_count}</span>
            </div>
          )}
        </div>

        {/* More reactions dropdown */}
        <div className="relative">
          <button className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded">
            More...
          </button>
        </div>
      </div>
    </div>
  );
};

export default IcebreakerResponseCard;