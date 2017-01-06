using System.Collections.Generic;
using Newtonsoft.Json;

namespace Sweetshot.Library.Models.Responses
{
    public class UserPostResponse
    {
        public int Count { get; set; }
        public string Next { get; set; }
        public string Previous { get; set; }
        public List<UserPost> Results { get; set; }
    }

    public class UserPost
    {
        public string Body { get; set; }
        public string Title { get; set; }
        public string Url { get; set; }
        public string Category { get; set; }
        public string Author { get; set; }
        public string Avatar { get; set; }

        [JsonProperty(PropertyName = "author_rewards")]
        public string AuthorRewards { get; set; }

        [JsonProperty(PropertyName = "author_reputation")]
        public string AuthorReputation { get; set; }

        [JsonProperty(PropertyName = "net_votes")]
        public string NetVotes { get; set; }

        public string Children { get; set; }

        public string Created { get; set; }
        [JsonProperty(PropertyName = "curator_payout_value")]
        public string CuratorPayoutValue { get; set; }

        [JsonProperty(PropertyName = "total_payout_value")]
        public string TotalPayoutValue { get; set; }

        [JsonProperty(PropertyName = "pending_payout_value")]
        public string PendingPayoutValue { get; set; }
        public List<string> Replies { get; set; }
        public int Vote { get; set; }
    }
}