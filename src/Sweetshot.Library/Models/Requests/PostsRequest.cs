using System;
using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class UserPostsRequest : SessionIdField
    {
        public UserPostsRequest(string sessionId, string username) : base(sessionId)
        {
            if (string.IsNullOrWhiteSpace(username))
            {
                throw new ArgumentNullException(nameof(username));
            }

            Username = username;
        }

        public string Username { get; private set; }
    }

    public class UserRecentPostsRequest : SessionIdField
    {
        public UserRecentPostsRequest(string sessionId) : base(sessionId)
        {
        }
    }

    public enum PostType
    {
        Top,
        Hot,
        New
    }

    public class PostsRequest : OffsetLimitFields
    {
        public PostsRequest(PostType type, string offset = "", int limit = 0) : base(offset, limit)
        {
            Type = type;
        }

        public PostType Type { get; private set; }
    }
}