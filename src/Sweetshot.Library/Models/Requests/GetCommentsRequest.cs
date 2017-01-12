using Sweetshot.Library.Models.Requests.Common;

namespace Sweetshot.Library.Models.Requests
{
    public class GetCommentsRequest : SessionIdField
    {
        public GetCommentsRequest(string sessionId, string url) : base(sessionId)
        {
            Url = url;
        }

        public string Url { get; private set; }
    }
}