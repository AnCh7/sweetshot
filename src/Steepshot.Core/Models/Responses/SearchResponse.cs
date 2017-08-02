using System.Collections.Generic;

namespace Steepshot.Core.Models.Responses
{
    public class SearchResponse
    {
        public int TotalCount { get; set; }
        public int Count { get; set; }
        public List<SearchResult> Results { get; set; }
    }

    public class SearchResult
    {
        public string Username { get; set; }
        public string ProfileImage { get; set; }
        public string Name { get; set; }
    }
}