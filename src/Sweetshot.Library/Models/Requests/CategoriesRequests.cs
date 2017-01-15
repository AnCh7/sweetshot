using System;
using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class CategoriesRequest : SessionIdField
    {
        public CategoriesRequest(string sessionId, string offset = "", int limit = 0) : base(sessionId)
        {
            Offset = offset;
            Limit = limit;
        }

        public string Offset { get; private set; }
        public int Limit { get; private set; }
    }

    public class SearchCategoriesRequest : SessionIdField
    {
        public SearchCategoriesRequest(string sessionId, string query) : base(sessionId)
        {
            if (string.IsNullOrWhiteSpace(query))
                throw new ArgumentNullException(nameof(query));
            if (query.Length <= 2)
                throw new ArgumentOutOfRangeException(nameof(query), "Min length is 3");

            Query = query;
        }

        public string Query { get; private set; }
    }
}