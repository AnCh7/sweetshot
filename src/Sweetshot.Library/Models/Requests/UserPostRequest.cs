using System;
using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class UserPostRequest : SessionIdField
    {
        public UserPostRequest(string sessionId, string username) : base(sessionId)
        {
            if (string.IsNullOrWhiteSpace(username))
            {
                throw new ArgumentNullException(nameof(username));
            }

            Username = username;
        }

        public string Username { get; private set; }
    }
}