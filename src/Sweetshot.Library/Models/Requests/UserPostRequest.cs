using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class UserPostRequest : SessionIdField
    {
        public UserPostRequest(string sessionId, string username) : base(sessionId)
        {
            Username = username;
        }

        public string Username { get; private set; }
    }
}