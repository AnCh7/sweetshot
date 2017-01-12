using Newtonsoft.Json;
using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public enum VoteType
    {
        Up,
        Down
    }

    public class VoteRequest : SessionIdField
    {
        public VoteRequest(string sessionId, VoteType type, string identifier) : base(sessionId)
        {
            Type = type;
            Identifier = identifier;
        }

        [JsonProperty(PropertyName = "identifier")]
        public string Identifier { get; private set; }

        public VoteType Type { get; private set; }
    }
}