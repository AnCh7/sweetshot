namespace Sweetshot.Library.Models.Requests
{
    public enum FriendsType
    {
        Followers,
        Following
    }

    public class UserFriendsRequest : UserRequest
    {
        public UserFriendsRequest(string sessionId, string username, FriendsType type) : base(sessionId, username)
        {
            Type = type;
        }

        public FriendsType Type { get; private set; }
    }
}