using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public enum FollowType
    {
        Follow,
        UnFollow
    }

    public class FollowRequest : SessionIdField
    {
        public FollowRequest(string sessionId, FollowType type, string username) : base(sessionId)
        {
            Username = username;
            Type = type;
        }

        public string Username { get; private set; }
        public FollowType Type { get; private set; }
    }
}