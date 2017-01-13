using System;
using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class TopPostRequest : SessionIdField
    {
        public TopPostRequest(string sessionId, int limit, string offset = "") : base(sessionId)
        {
            if (limit < 0)
            {
                throw new ArgumentException(nameof(limit));
            }

            Limit = limit;
            Offset = offset;
        }

        public int Limit { get; private set; }

        public string Offset { get; private set; }
    }
}