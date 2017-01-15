namespace Sweetshot.Library.Models.Requests
{
    public enum FriendsType
    {
        Followers,
        Following
    }

    public class UserFriendsRequest : UserPostsRequest
    {
        public UserFriendsRequest(string sessionId, string username, FriendsType type, string offset = "", int limit = 0)
            : base(sessionId, username)
        {
            Type = type;
            Offset = offset;
            Limit = limit;
        }

        public FriendsType Type { get; private set; }
        public string Offset { get; private set; }
        public int Limit { get; private set; }
    }
}