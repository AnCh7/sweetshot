using System;
using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public enum PostType
    {
        Top,
        Hot,
        New
    }

    public class PostsRequest : SessionIdField
    {
        public PostsRequest(string sessionId, PostType type, int limit = 0, string offset = "") : base(sessionId)
        {
            Type = type;
            Limit = limit;
            Offset = offset;
        }

        public PostType Type { get; private set; }

        public int Limit { get; private set; }

        public string Offset { get; private set; }
    }
}