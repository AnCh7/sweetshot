﻿using System;
using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class SearchCategoriesRequest : SessionIdField
    {
        public SearchCategoriesRequest(string sessionId, string query) : base(sessionId)
        {
            if (string.IsNullOrWhiteSpace(query))
            {
                throw new ArgumentNullException(nameof(query));
            }

            Query = query;
        }

        public string Query { get; private set; }
    }
}