namespace Sweetshot.Library.Models.Requests
{
    public class FollowRequest : SessionIdField
    {
        public FollowRequest(string token, string _username) : base(token)
        {
            username = _username;
        }

        public string username { get; private set; }
    }
}